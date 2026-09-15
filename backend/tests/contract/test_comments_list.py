from app.models.user import Role


def test_list_comments_returns_thread_in_order(client, make_user, make_meeting, make_task, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    client.post(f"/api/tasks/{task.id}/comments", json={"message": "First"}, headers=auth_header(owner))
    client.post(f"/api/tasks/{task.id}/comments", json={"message": "Second"}, headers=auth_header(sarah))

    response = client.get(f"/api/tasks/{task.id}/comments", headers=auth_header(sarah))

    assert response.status_code == 200
    messages = [comment["message"] for comment in response.json()]
    assert messages == ["First", "Second"]


def test_list_comments_on_unknown_task_returns_404(client, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)

    response = client.get("/api/tasks/999999/comments", headers=auth_header(owner))

    assert response.status_code == 404
