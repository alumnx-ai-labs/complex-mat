from fastapi.testclient import TestClient

from app.models.user import Role


def _create_meeting(client, headers, title, date, attendee_ids):
    return client.post(
        "/api/meetings",
        json={"title": title, "date": date, "time": "14:00", "attendeeIds": attendee_ids},
        headers=headers,
    ).json()


def test_admin_and_team_member_each_see_correct_meetings_with_accurate_task_counts_and_can_open_them(
    client: TestClient, make_user, auth_header
):
    admin, _ = make_user(role=Role.ADMIN)
    member, _ = make_user(role=Role.TEAM_MEMBER)
    outsider, _ = make_user(role=Role.TEAM_MEMBER)

    invited = _create_meeting(client, auth_header(admin), "Q3 Roadmap Review", "2026-09-10", [member.id])
    not_invited = _create_meeting(
        client, auth_header(admin), "Leadership Sync", "2026-09-11", [outsider.id]
    )

    for i in range(3):
        client.post(
            f"/api/meetings/{invited['id']}/tasks",
            json={"title": f"Task {i}", "assigneeId": member.id},
            headers=auth_header(admin),
        )

    # Admin sees every meeting, each with its correct task count.
    admin_view = client.get("/api/meetings", headers=auth_header(admin)).json()
    admin_by_id = {m["id"]: m for m in admin_view}
    assert admin_by_id[invited["id"]]["title"] == "Q3 Roadmap Review"
    assert admin_by_id[invited["id"]]["date"] == "2026-09-10"
    assert admin_by_id[invited["id"]]["taskCount"] == 3
    assert admin_by_id[not_invited["id"]]["taskCount"] == 0

    # A Team Member only sees meetings they were invited to.
    member_view = client.get("/api/meetings", headers=auth_header(member)).json()
    member_ids = {m["id"] for m in member_view}
    assert invited["id"] in member_ids
    assert not_invited["id"] not in member_ids
    member_entry = next(m for m in member_view if m["id"] == invited["id"])
    assert member_entry["taskCount"] == 3

    # Selecting a permitted meeting opens its full details.
    detail = client.get(f"/api/meetings/{invited['id']}", headers=auth_header(member))
    assert detail.status_code == 200
    assert detail.json()["title"] == "Q3 Roadmap Review"
    assert len(detail.json()["tasks"]) == 3

    # The Team Member who was never invited cannot open it directly either.
    forbidden = client.get(f"/api/meetings/{invited['id']}", headers=auth_header(outsider))
    assert forbidden.status_code == 403
