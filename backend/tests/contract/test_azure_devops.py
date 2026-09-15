from app.main import app
from app.integrations.azure_devops_client import AdoWorkItem, AzureDevOpsClient, get_azure_devops_client
from app.models.user import Role


class _FakeAdoClient(AzureDevOpsClient):
    def __init__(self, known: dict[int, AdoWorkItem]):
        self._known = known

    def get(self, work_item_id: int):
        return self._known.get(work_item_id)

    def search(self, query: str):
        if not query.isdigit():
            return []
        item = self._known.get(int(query))
        return [item] if item else []


def test_suggestions_empty_when_azure_devops_unconfigured(client, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)

    response = client.get("/api/azure-devops/suggestions?q=123", headers=auth_header(owner))

    assert response.status_code == 200
    assert response.json() == []


def test_suggestions_returns_matches_from_client(client, make_user, auth_header):
    app.dependency_overrides[get_azure_devops_client] = lambda: _FakeAdoClient(
        {1234: AdoWorkItem(id=1234, title="Implement onboarding API", type="Story")}
    )
    owner, _ = make_user(role=Role.ADMIN)

    response = client.get("/api/azure-devops/suggestions?q=1234", headers=auth_header(owner))

    assert response.status_code == 200
    assert response.json() == [
        {"adoWorkItemId": 1234, "title": "Implement onboarding API", "type": "Story"}
    ]


def test_task_references_reflect_current_availability(
    client, make_user, make_meeting, make_task, auth_header
):
    app.dependency_overrides[get_azure_devops_client] = lambda: _FakeAdoClient(
        {1234: AdoWorkItem(id=1234, title="Implement onboarding API", type="Story")}
    )
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah, description_notes="See @1234 for context")

    response = client.patch(
        f"/api/tasks/{task.id}",
        json={"descriptionNotes": "See @1234 for context"},
        headers=auth_header(sarah),
    )
    assert response.status_code == 200

    refs_response = client.get(f"/api/tasks/{task.id}/ado-references", headers=auth_header(sarah))
    assert refs_response.status_code == 200
    assert refs_response.json() == [
        {
            "adoWorkItemId": 1234,
            "title": "Implement onboarding API",
            "type": "Story",
            "isAvailable": True,
            "openUrl": None,
        }
    ]

    # The work item becomes unavailable (deleted/inaccessible) after the reference was created.
    app.dependency_overrides[get_azure_devops_client] = lambda: _FakeAdoClient({})
    refs_response = client.get(f"/api/tasks/{task.id}/ado-references", headers=auth_header(sarah))
    assert refs_response.status_code == 200
    body = refs_response.json()[0]
    assert body["isAvailable"] is False
    assert body["openUrl"] is None
    assert body["title"] == "Implement onboarding API"


def test_task_references_on_unknown_task_returns_404(client, make_user, auth_header):
    owner, _ = make_user(role=Role.ADMIN)

    response = client.get("/api/tasks/999999/ado-references", headers=auth_header(owner))

    assert response.status_code == 404
