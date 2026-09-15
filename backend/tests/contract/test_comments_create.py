from app.main import app
from app.integrations.azure_devops_client import AdoWorkItem, AzureDevOpsClient, get_azure_devops_client
from app.models.user import Role


class _FakeAdoClient(AzureDevOpsClient):
    def __init__(self):
        pass

    def get(self, work_item_id: int):
        if work_item_id == 1234:
            return AdoWorkItem(id=1234, title="Implement onboarding API", type="Story")
        return None

    def search(self, query: str):
        item = self.get(int(query)) if query.isdigit() else None
        return [item] if item else []


def _use_fake_ado_client():
    app.dependency_overrides[get_azure_devops_client] = lambda: _FakeAdoClient()


def test_owner_can_post_comment(client, make_user, make_meeting, make_task, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Please take a look"},
        headers=auth_header(owner),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Please take a look"
    assert body["authorName"] == owner.employee_name


def test_assignee_can_post_comment(client, make_user, make_meeting, make_task, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "On it"},
        headers=auth_header(sarah),
    )

    assert response.status_code == 201


def test_other_admin_can_post_comment(client, make_user, make_meeting, make_task, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Admin checking in"},
        headers=auth_header(other_admin),
    )

    assert response.status_code == 201


def test_unrelated_attendee_cannot_post_comment(client, make_user, make_meeting, make_task, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    bystander, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah, bystander])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Not my task"},
        headers=auth_header(bystander),
    )

    assert response.status_code == 403


def test_empty_message_is_rejected(client, make_user, make_meeting, make_task, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "   "},
        headers=auth_header(owner),
    )

    assert response.status_code == 422


def test_comment_on_unknown_task_returns_404(client, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)

    response = client.post(
        "/api/tasks/999999/comments",
        json={"message": "Hello"},
        headers=auth_header(owner),
    )

    assert response.status_code == 404


def test_letter_mention_resolves_to_attendee(client, make_user, make_meeting, make_task, auth_header):
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER, employee_name="Sarah Iyer")
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Can @Sarah confirm this?"},
        headers=auth_header(owner),
    )

    assert response.status_code == 201
    mentions = response.json()["mentions"]
    assert len(mentions) == 1
    assert mentions[0]["userId"] == sarah.id


def test_digit_token_becomes_ado_reference(client, make_user, make_meeting, make_task, auth_header):
    _use_fake_ado_client()
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Related to @1234"},
        headers=auth_header(owner),
    )

    assert response.status_code == 201
    ado_references = response.json()["adoReferences"]
    assert ado_references == [
        {
            "adoWorkItemId": 1234,
            "title": "Implement onboarding API",
            "type": "Story",
            "isAvailable": True,
        }
    ]


def test_unresolvable_ado_token_shows_unavailable(client, make_user, make_meeting, make_task, auth_header):
    _use_fake_ado_client()
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    response = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Related to @9999"},
        headers=auth_header(owner),
    )

    assert response.status_code == 201
    ado_references = response.json()["adoReferences"]
    assert ado_references == [
        {"adoWorkItemId": 9999, "title": None, "type": None, "isAvailable": False}
    ]
