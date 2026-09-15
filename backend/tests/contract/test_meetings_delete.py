from fastapi.testclient import TestClient

from app.models.activity_log import ActivityLogEntry
from app.models.user import Role


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


def test_any_admin_can_delete_a_meeting_they_do_not_own(client: TestClient, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    meeting_id = _create_meeting(client, auth_header(owner), [])

    response = client.delete(f"/api/meetings/{meeting_id}", headers=auth_header(other_admin))

    assert response.status_code == 204
    assert client.get(f"/api/meetings/{meeting_id}", headers=auth_header(owner)).status_code == 404


def test_team_member_cannot_delete_a_meeting(client: TestClient, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    member, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [member.id])

    response = client.delete(f"/api/meetings/{meeting_id}", headers=auth_header(member))

    assert response.status_code == 403


def test_deleting_an_unknown_meeting_returns_404(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.delete("/api/meetings/999999", headers=auth_header(admin))

    assert response.status_code == 404


def test_deleting_a_meeting_cascades_to_its_tasks_and_removes_them_from_my_tasks(
    client: TestClient, make_user, auth_header
):
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [assignee.id])
    client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Prepare notes", "assigneeId": assignee.id},
        headers=auth_header(owner),
    )

    response = client.delete(f"/api/meetings/{meeting_id}", headers=auth_header(owner))

    assert response.status_code == 204
    my_tasks = client.get("/api/tasks/mine", headers=auth_header(assignee)).json()
    assert my_tasks == []


def test_deleting_a_meeting_cleans_up_task_comments_and_mentions_without_error(
    client: TestClient, make_user, auth_header
):
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [assignee.id])
    task = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Prepare notes", "assigneeId": assignee.id},
        headers=auth_header(owner),
    ).json()
    comment_response = client.post(
        f"/api/tasks/{task['id']}/comments",
        json={"message": f"cc @{assignee.employee_name}"},
        headers=auth_header(owner),
    )
    assert comment_response.status_code == 201

    response = client.delete(f"/api/meetings/{meeting_id}", headers=auth_header(owner))

    assert response.status_code == 204


def test_deleting_a_meeting_records_a_single_activity_log_entry(
    client: TestClient, make_user, auth_header, db_session
):
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [assignee.id])
    client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Task one", "assigneeId": assignee.id},
        headers=auth_header(owner),
    )
    client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Task two", "assigneeId": assignee.id},
        headers=auth_header(owner),
    )

    response = client.delete(f"/api/meetings/{meeting_id}", headers=auth_header(owner))
    assert response.status_code == 204

    entries = (
        db_session.query(ActivityLogEntry)
        .filter_by(entity_type="Meeting", entity_id=meeting_id, action="MEETING_DELETED")
        .all()
    )
    assert len(entries) == 1
