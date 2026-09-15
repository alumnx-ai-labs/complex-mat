from fastapi.testclient import TestClient

from app.models.user import Role


def _create_meeting(client, headers, attendee_ids, agenda="Original agenda"):
    response = client.post(
        "/api/meetings",
        json={
            "title": "Q3 Roadmap Review",
            "date": "2026-09-15",
            "time": "14:00",
            "agendaNotes": agenda,
            "attendeeIds": attendee_ids,
        },
        headers=headers,
    )
    return response.json()["id"]


def test_non_owner_admin_edits_agenda_then_deletes_meeting_and_tasks_vanish_everywhere(
    client: TestClient, make_user, auth_header
):
    owner, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_id = _create_meeting(client, auth_header(owner), [assignee.id])
    task = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Prepare notes", "assigneeId": assignee.id},
        headers=auth_header(owner),
    ).json()

    edit_response = client.patch(
        f"/api/meetings/{meeting_id}",
        json={"agendaNotes": "Revised agenda from a different Admin."},
        headers=auth_header(other_admin),
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["agendaNotes"] == "Revised agenda from a different Admin."
    assert edit_response.json()["ownerId"] == owner.id

    before = client.get("/api/tasks/mine", headers=auth_header(assignee)).json()
    assert any(t["id"] == task["id"] for t in before)

    delete_response = client.delete(f"/api/meetings/{meeting_id}", headers=auth_header(other_admin))
    assert delete_response.status_code == 204

    assert client.get(f"/api/meetings/{meeting_id}", headers=auth_header(owner)).status_code == 404
    after = client.get("/api/tasks/mine", headers=auth_header(assignee)).json()
    assert after == []


def test_removed_assignee_keeps_their_task_and_can_still_act_on_it(
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

    client.patch(
        f"/api/meetings/{meeting_id}",
        json={"attendeeIds": []},
        headers=auth_header(owner),
    )

    detail = client.get(f"/api/meetings/{meeting_id}", headers=auth_header(owner)).json()
    updated_task = next(t for t in detail["tasks"] if t["id"] == task["id"])
    assert updated_task["needsReassignment"] is True
    assert updated_task["assigneeId"] == assignee.id

    status_response = client.patch(
        f"/api/tasks/{task['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=auth_header(assignee),
    )
    assert status_response.status_code == 200
