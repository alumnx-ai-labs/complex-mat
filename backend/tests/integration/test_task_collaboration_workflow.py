"""Integration coverage for User Story 5 - Collaborate via Comments, Mentions,
and Azure DevOps References (spec.md Acceptance Scenarios 1-6), exercising the
comments, mention-search, and Azure DevOps endpoints together against a real
DB/session rather than one endpoint in isolation.
"""

from app.integrations.azure_devops_client import AdoWorkItem, AzureDevOpsClient, get_azure_devops_client
from app.main import app
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


def _use_ado_client(known: dict[int, AdoWorkItem]) -> None:
    app.dependency_overrides[get_azure_devops_client] = lambda: _FakeAdoClient(known)


def test_comment_with_mention_and_ado_reference_are_disambiguated(
    client, make_user, make_meeting, make_task, auth_header
):
    """Independent Test (spec.md US5): a comment mentioning an attendee
    ("@Sarah") and referencing a work item ("@1234") in the same message
    renders the mention as a member reference and the numeric token as a
    distinct Linked Azure DevOps Item with an Open action (AC2, AC3, AC4)."""
    _use_ado_client({1234: AdoWorkItem(id=1234, title="Implement onboarding API", type="Story")})

    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER, employee_name="Sarah Iyer")
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    # "@" + letters opens a mention search scoped to this meeting's Attendees (AC2)
    mention_results = client.get(
        f"/api/meetings/{meeting.id}/attendees/mention-search?q=Sar",
        headers=auth_header(owner),
    )
    assert mention_results.status_code == 200
    assert any(user["id"] == sarah.id for user in mention_results.json())

    # "@" + digits surfaces Azure DevOps Story/Feature suggestions instead (AC3)
    ado_suggestions = client.get(
        "/api/azure-devops/suggestions?q=1234", headers=auth_header(owner)
    )
    assert ado_suggestions.status_code == 200
    assert ado_suggestions.json() == [
        {"adoWorkItemId": 1234, "title": "Implement onboarding API", "type": "Story"}
    ]

    # Posting a comment with both tokens together disambiguates each one (AC2, AC3, AC4)
    posted = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Can @Sarah confirm this lines up with @1234?"},
        headers=auth_header(owner),
    )
    assert posted.status_code == 201
    body = posted.json()
    assert body["mentions"] == [{"userId": sarah.id, "employeeName": "Sarah Iyer"}]
    assert body["adoReferences"] == [
        {
            "adoWorkItemId": 1234,
            "title": "Implement onboarding API",
            "type": "Story",
            "isAvailable": True,
        }
    ]

    # The comment thread persists both, in order, for anyone viewing the Task
    thread = client.get(f"/api/tasks/{task.id}/comments", headers=auth_header(sarah))
    assert thread.status_code == 200
    assert thread.json()[0]["mentions"][0]["userId"] == sarah.id
    assert thread.json()[0]["adoReferences"][0]["adoWorkItemId"] == 1234


def test_only_owner_assignee_or_admin_may_comment(
    client, make_user, make_meeting, make_task, auth_header
):
    """AC1: comment posting is restricted to the parent Meeting's Owner, the
    Task's Assignee, or any Admin - no one else."""
    owner, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    bystander, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah, bystander])
    task = make_task(meeting, sarah)

    for permitted_user in (owner, sarah, other_admin):
        response = client.post(
            f"/api/tasks/{task.id}/comments",
            json={"message": f"Note from {permitted_user.employee_name}"},
            headers=auth_header(permitted_user),
        )
        assert response.status_code == 201

    forbidden = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "I shouldn't be able to post this"},
        headers=auth_header(bystander),
    )
    assert forbidden.status_code == 403

    thread = client.get(f"/api/tasks/{task.id}/comments", headers=auth_header(sarah))
    assert len(thread.json()) == 3


def test_ado_token_in_task_description_becomes_a_linked_item(
    client, make_user, make_meeting, make_task, auth_header
):
    """AC4: an '@<number>' token typed in a Task's Description/Notes (not
    just a Comment) is treated as a Linked Azure DevOps Item, with no
    separate reference field to fill in."""
    _use_ado_client({1234: AdoWorkItem(id=1234, title="Implement onboarding API", type="Story")})

    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    updated = client.patch(
        f"/api/tasks/{task.id}",
        json={"descriptionNotes": "Blocked on @1234 until design review completes."},
        headers=auth_header(sarah),
    )
    assert updated.status_code == 200

    references = client.get(f"/api/tasks/{task.id}/ado-references", headers=auth_header(sarah))
    assert references.status_code == 200
    assert references.json() == [
        {
            "adoWorkItemId": 1234,
            "title": "Implement onboarding API",
            "type": "Story",
            "isAvailable": True,
            "openUrl": None,
        }
    ]


def test_linked_item_shows_unavailable_after_work_item_is_deleted(
    client, make_user, make_meeting, make_task, auth_header
):
    """AC5: once a Linked Azure DevOps Item's underlying work item is deleted
    or becomes inaccessible, the Task still shows the reference with an
    "unavailable" indicator and the Open action disabled."""
    _use_ado_client({1234: AdoWorkItem(id=1234, title="Implement onboarding API", type="Story")})

    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)

    client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Tracked in @1234"},
        headers=auth_header(owner),
    )

    still_there = client.get(f"/api/tasks/{task.id}/ado-references", headers=auth_header(sarah))
    assert still_there.json()[0]["isAvailable"] is True

    # The work item is deleted/becomes inaccessible in Azure DevOps.
    _use_ado_client({})

    after_deletion = client.get(f"/api/tasks/{task.id}/ado-references", headers=auth_header(sarah))
    assert after_deletion.status_code == 200
    body = after_deletion.json()[0]
    assert body["isAvailable"] is False
    assert body["openUrl"] is None
    assert body["title"] == "Implement onboarding API"  # last-known title stays visible


def test_task_stays_usable_when_azure_devops_is_unreachable(
    client, make_user, make_meeting, make_task, auth_header
):
    """AC6: when Azure DevOps is temporarily unavailable, everything about
    the Task keeps working except "@<number>" suggestion lookups."""
    owner, _ = make_user(role=Role.ADMIN)
    sarah, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [sarah])
    task = make_task(meeting, sarah)
    # No dependency override is installed - AzureDevOpsClient falls back to
    # its default (unconfigured) settings, simulating Azure DevOps being
    # unreachable/not configured.

    suggestions = client.get("/api/azure-devops/suggestions?q=1234", headers=auth_header(owner))
    assert suggestions.status_code == 200
    assert suggestions.json() == []

    comment = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": "Still tracking this in @1234, will update once linked."},
        headers=auth_header(owner),
    )
    assert comment.status_code == 201

    description_update = client.patch(
        f"/api/tasks/{task.id}",
        json={"descriptionNotes": "Updated while Azure DevOps is down."},
        headers=auth_header(sarah),
    )
    assert description_update.status_code == 200

    status_update = client.patch(
        f"/api/tasks/{task.id}/status",
        json={"status": "IN_PROGRESS"},
        headers=auth_header(sarah),
    )
    assert status_update.status_code == 200

    references = client.get(f"/api/tasks/{task.id}/ado-references", headers=auth_header(sarah))
    assert references.status_code == 200
    assert references.json()[0]["isAvailable"] is False
