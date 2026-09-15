from fastapi.testclient import TestClient

from app.models.user import Role


def _create_meeting(client, headers, attendee_ids):
    response = client.post(
        "/api/meetings",
        json={
            "title": "Q3 Roadmap Review",
            "date": "2026-09-15",
            "time": "14:00",
            "agendaNotes": "Discuss roadmap.",
            "attendeeIds": attendee_ids,
        },
        headers=headers,
    )
    return response.json()["id"]


def test_any_admin_can_edit_a_meeting_they_do_not_own(client: TestClient, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    attendee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [attendee.id])

    response = client.patch(
        f"/api/meetings/{meeting_id}",
        json={
            "title": "Q3 Roadmap Review (rescheduled)",
            "date": "2026-09-16",
            "time": "15:00",
            "agendaNotes": "Updated agenda.",
        },
        headers=auth_header(other_admin),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Q3 Roadmap Review (rescheduled)"
    assert body["date"] == "2026-09-16"
    assert body["time"] == "15:00:00"
    assert body["agendaNotes"] == "Updated agenda."


def test_team_member_cannot_edit_a_meeting(client: TestClient, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    member, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [member.id])

    response = client.patch(
        f"/api/meetings/{meeting_id}",
        json={"title": "Hijacked"},
        headers=auth_header(member),
    )

    assert response.status_code == 403


def test_owner_field_cannot_be_changed_via_edit(client: TestClient, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    meeting_id = _create_meeting(client, auth_header(owner), [])

    response = client.patch(
        f"/api/meetings/{meeting_id}",
        json={"title": "Still same owner", "ownerId": other_admin.id},
        headers=auth_header(other_admin),
    )

    assert response.status_code == 200
    assert response.json()["ownerId"] == owner.id


def test_removing_a_tasks_assignee_from_attendees_flags_needs_reassignment(
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

    response = client.patch(
        f"/api/meetings/{meeting_id}",
        json={"attendeeIds": []},
        headers=auth_header(owner),
    )

    assert response.status_code == 200
    body = response.json()
    updated_task = next(t for t in body["tasks"] if t["id"] == task["id"])
    assert updated_task["assigneeId"] == assignee.id
    assert updated_task["needsReassignment"] is True


def test_editing_with_an_inactive_attendee_is_rejected(client: TestClient, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    inactive, _ = make_user(role=Role.TEAM_MEMBER, is_active=False)
    meeting_id = _create_meeting(client, auth_header(owner), [])

    response = client.patch(
        f"/api/meetings/{meeting_id}",
        json={"attendeeIds": [inactive.id]},
        headers=auth_header(owner),
    )

    assert response.status_code == 422


def test_editing_an_unknown_meeting_returns_404(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.patch(
        "/api/meetings/999999",
        json={"title": "Ghost"},
        headers=auth_header(admin),
    )

    assert response.status_code == 404
