from fastapi.testclient import TestClient

from app.models.user import Role
from tests.conftest import RecordingEmailSender


def _create_meeting(client, headers, attendee_ids):
    response = client.post(
        "/api/meetings",
        json={
            "title": "Q3 Roadmap Review",
            "date": "2026-09-15",
            "time": "14:00",
            "attendeeIds": attendee_ids,
        },
        headers=headers,
    )
    return response.json()["id"]


def test_assigning_a_task_emails_the_assignee(
    client: TestClient, make_user, auth_header, email_sender_spy: RecordingEmailSender
):
    owner, _ = make_user(role=Role.ADMIN)
    attendee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [attendee.id])

    response = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={
            "title": "Prepare onboarding design doc",
            "assigneeId": attendee.id,
            "dueDate": "2026-09-20",
        },
        headers=auth_header(owner),
    )

    assert response.status_code == 201
    assert len(email_sender_spy.sent) == 1
    to_email, subject, body = email_sender_spy.sent[0]
    assert to_email == attendee.employee_mail_id
    assert "Prepare onboarding design doc" in subject
    assert "Q3 Roadmap Review" in body
    assert "2026-09-20" in body


def test_reassigning_a_task_emails_the_new_assignee_only(
    client: TestClient, make_user, auth_header, email_sender_spy: RecordingEmailSender
):
    owner, _ = make_user(role=Role.ADMIN)
    attendee_a, _ = make_user(role=Role.TEAM_MEMBER)
    attendee_b, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [attendee_a.id, attendee_b.id])

    created = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Prepare notes", "assigneeId": attendee_a.id},
        headers=auth_header(owner),
    ).json()
    email_sender_spy.sent.clear()

    response = client.patch(
        f"/api/tasks/{created['id']}",
        json={"assigneeId": attendee_b.id},
        headers=auth_header(owner),
    )

    assert response.status_code == 200
    assert len(email_sender_spy.sent) == 1
    assert email_sender_spy.sent[0][0] == attendee_b.employee_mail_id


def test_reassigning_to_the_same_assignee_does_not_send_a_duplicate_email(
    client: TestClient, make_user, auth_header, email_sender_spy: RecordingEmailSender
):
    owner, _ = make_user(role=Role.ADMIN)
    attendee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [attendee.id])

    created = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Prepare notes", "assigneeId": attendee.id},
        headers=auth_header(owner),
    ).json()
    email_sender_spy.sent.clear()

    response = client.patch(
        f"/api/tasks/{created['id']}",
        json={"assigneeId": attendee.id},
        headers=auth_header(owner),
    )

    assert response.status_code == 200
    assert email_sender_spy.sent == []


def test_forbidden_reassignment_attempt_sends_no_email(
    client: TestClient, make_user, auth_header, email_sender_spy: RecordingEmailSender
):
    owner, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    attendee_a, _ = make_user(role=Role.TEAM_MEMBER)
    attendee_b, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [attendee_a.id, attendee_b.id])

    created = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Prepare notes", "assigneeId": attendee_a.id},
        headers=auth_header(owner),
    ).json()
    email_sender_spy.sent.clear()

    response = client.patch(
        f"/api/tasks/{created['id']}",
        json={"assigneeId": attendee_b.id},
        headers=auth_header(other_admin),
    )

    assert response.status_code == 403
    assert email_sender_spy.sent == []


def test_status_update_does_not_trigger_an_assignment_email(
    client: TestClient, make_user, auth_header, email_sender_spy: RecordingEmailSender
):
    owner, _ = make_user(role=Role.ADMIN)
    attendee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [attendee.id])

    created = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Prepare notes", "assigneeId": attendee.id},
        headers=auth_header(owner),
    ).json()
    email_sender_spy.sent.clear()

    response = client.patch(
        f"/api/tasks/{created['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=auth_header(attendee),
    )

    assert response.status_code == 200
    assert email_sender_spy.sent == []


def test_email_delivery_failure_does_not_block_task_creation(
    client: TestClient, make_user, auth_header
):
    from app.integrations.email_sender import get_email_sender
    from app.main import app

    class BrokenEmailSender:
        def send(self, to_email: str, subject: str, body: str) -> None:
            raise RuntimeError("SMTP is down")

    app.dependency_overrides[get_email_sender] = lambda: BrokenEmailSender()
    try:
        owner, _ = make_user(role=Role.ADMIN)
        attendee, _ = make_user(role=Role.TEAM_MEMBER)
        meeting_id = _create_meeting(client, auth_header(owner), [attendee.id])

        response = client.post(
            f"/api/meetings/{meeting_id}/tasks",
            json={"title": "Prepare notes", "assigneeId": attendee.id},
            headers=auth_header(owner),
        )

        assert response.status_code == 201
    finally:
        del app.dependency_overrides[get_email_sender]
