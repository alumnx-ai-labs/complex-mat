"""Integration coverage for User Story 9 - Admin Manages Member Accounts, Roles,
and Access (spec.md Acceptance Scenarios 1-7), exercising the People (users)
endpoints together against a real DB/session rather than one endpoint in
isolation.
"""

from sqlalchemy.orm import Session

from app.models.user import Role
from app.models.workspace_settings import WorkspaceSettings


def test_admin_manages_a_members_full_lifecycle(client, make_user, auth_header):
    """Independent Test (spec.md US9): an Admin adds a new member, confirms
    they can sign in, changes their Role and resets their Password, then
    deactivates them and confirms they can no longer sign in or appear in
    attendee/assignee search (AC2-AC6)."""
    admin, _ = make_user(role=Role.ADMIN)

    created = client.post(
        "/api/users",
        json={
            "employeeName": "Priya Nair",
            "employeeMailId": "priya@example.com",
            "employeeId": "EMP-1077",
            "password": "TempPass123!",
            "role": "TEAM_MEMBER",
        },
        headers=auth_header(admin),
    )
    assert created.status_code == 201
    member_id = created.json()["id"]

    login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": "priya@example.com",
            "password": "TempPass123!",
            "termsAccepted": True,
        },
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "TEAM_MEMBER"

    role_change = client.patch(
        f"/api/users/{member_id}/role",
        json={"role": "ADMIN"},
        headers=auth_header(admin),
    )
    assert role_change.status_code == 200

    reset = client.patch(
        f"/api/users/{member_id}/password",
        json={"password": "NewTempPass456!"},
        headers=auth_header(admin),
    )
    assert reset.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": "priya@example.com",
            "password": "TempPass123!",
            "termsAccepted": True,
        },
    )
    assert old_login.status_code == 401

    deactivate = client.patch(
        f"/api/users/{member_id}/active",
        json={"isActive": False},
        headers=auth_header(admin),
    )
    assert deactivate.status_code == 200

    blocked_login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": "priya@example.com",
            "password": "NewTempPass456!",
            "termsAccepted": True,
        },
    )
    assert blocked_login.status_code == 401

    search = client.get("/api/users", params={"q": "Priya"}, headers=auth_header(admin))
    assert member_id not in {u["id"] for u in search.json()}


def test_deactivating_a_meeting_owner_transfers_ownership_of_their_meetings(
    client, make_user, make_meeting, auth_header, db_session: Session
):
    """AC7: deactivating a member who owns Meetings transfers ownership of
    every one of those Meetings to the workspace's configured default Admin."""
    default_admin, _ = make_user(role=Role.ADMIN)
    db_session.add(WorkspaceSettings(id=1, default_admin_user_id=default_admin.id))
    db_session.commit()

    owner_admin, _ = make_user(role=Role.ADMIN)
    attendee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner_admin, [attendee])

    deactivate = client.patch(
        f"/api/users/{owner_admin.id}/active",
        json={"isActive": False},
        headers=auth_header(default_admin),
    )
    assert deactivate.status_code == 200

    meeting_detail = client.get(f"/api/meetings/{meeting.id}", headers=auth_header(default_admin))
    assert meeting_detail.status_code == 200
    assert meeting_detail.json()["ownerId"] == default_admin.id


def test_deactivating_a_members_tasks_are_flagged_for_reassignment(
    client, make_user, make_meeting, make_task, auth_header
):
    """FR-024: deactivating a member who is the Assignee of one or more Tasks
    flags each of those Tasks as needing reassignment, without changing who
    they're still (invalidly) assigned to."""
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [assignee])
    task = make_task(meeting, assignee)

    deactivate = client.patch(
        f"/api/users/{assignee.id}/active",
        json={"isActive": False},
        headers=auth_header(owner),
    )
    assert deactivate.status_code == 200

    detail = client.get(f"/api/meetings/{meeting.id}", headers=auth_header(owner))
    updated_task = next(t for t in detail.json()["tasks"] if t["id"] == task.id)
    assert updated_task["needsReassignment"] is True
    assert updated_task["assigneeId"] == assignee.id
