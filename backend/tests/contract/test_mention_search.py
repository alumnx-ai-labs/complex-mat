from app.models.user import Role


def test_mention_search_is_scoped_to_meeting_attendees(client, make_user, make_meeting, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    outsider, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])

    response = client.get(
        f"/api/meetings/{meeting.id}/attendees/mention-search",
        headers=auth_header(owner),
    )

    assert response.status_code == 200
    ids = {user["id"] for user in response.json()}
    assert sarah.id in ids
    assert outsider.id not in ids


def test_mention_search_filters_by_query(client, make_user, make_meeting, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER, employee_name="Sarah Iyer")
    meeting = make_meeting(owner, [sarah])

    response = client.get(
        f"/api/meetings/{meeting.id}/attendees/mention-search?q=zzz",
        headers=auth_header(owner),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_mention_search_on_unknown_meeting_returns_404(client, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)

    response = client.get(
        "/api/meetings/999999/attendees/mention-search",
        headers=auth_header(owner),
    )

    assert response.status_code == 404
