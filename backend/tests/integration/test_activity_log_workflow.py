"""Integration coverage for User Story 10 - Admin Reviews the Activity Log
(spec.md Acceptance Scenarios 1-3), exercising the Activity Log endpoint
together with the Meeting/Task/People endpoints whose actions it records.
"""

from app.models.user import Role
from app.models.task import TaskStatus


def test_meeting_task_and_member_actions_all_appear_in_the_activity_log(
    client, make_user, auth_header
):
    """Independent Test (spec.md US10): create a meeting, assign a task, add a
    member, then confirm each appears in the Activity Log with its actor and
    timestamp (AC2)."""
    admin, _ = make_user(role=Role.ADMIN)
    attendee, _ = make_user(role=Role.TEAM_MEMBER)

    meeting = client.post(
        "/api/meetings",
        json={
            "title": "Roadmap Sync",
            "date": "2026-09-20",
            "time": "10:00:00",
            "agendaNotes": None,
            "attendeeIds": [attendee.id],
        },
        headers=auth_header(admin),
    )
    assert meeting.status_code == 201
    meeting_id = meeting.json()["id"]

    task = client.post(
        f"/api/meetings/{meeting_id}/tasks",
        json={"title": "Draft the roadmap doc", "assigneeId": attendee.id},
        headers=auth_header(admin),
    )
    assert task.status_code == 201

    member = client.post(
        "/api/users",
        json={
            "employeeName": "New Hire",
            "employeeMailId": "new.hire@example.com",
            "employeeId": "EMP-2001",
            "password": "TempPass123!",
            "role": "TEAM_MEMBER",
        },
        headers=auth_header(admin),
    )
    assert member.status_code == 201

    log = client.get("/api/activity-log", headers=auth_header(admin))
    assert log.status_code == 200
    actions = {entry["action"] for entry in log.json()}
    assert {"MEETING_CREATED", "TASK_CREATED", "MEMBER_ADDED"} <= actions
    for entry in log.json():
        assert entry["actorId"] == admin.id
        assert entry["actorName"] == admin.employee_name
        assert entry["timestamp"]


def test_deleting_a_meeting_records_the_cascading_task_deletion(
    client, make_user, make_meeting, make_task, auth_header
):
    """AC3: deleting a Meeting that has Tasks records the cascading deletion
    as an Activity Log entry."""
    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(admin, [assignee])
    make_task(meeting, assignee)

    delete = client.delete(f"/api/meetings/{meeting.id}", headers=auth_header(admin))
    assert delete.status_code == 204

    log = client.get("/api/activity-log", headers=auth_header(admin))
    actions = [entry["action"] for entry in log.json()]
    assert "MEETING_DELETED" in actions


def test_mentioning_a_member_in_a_comment_appears_in_the_activity_log(
    client, make_user, make_meeting, make_task, auth_header
):
    """AC2: mentioning a member is recorded in the Activity Log."""
    owner, _ = make_user(role=Role.ADMIN)
    mentioned, _ = make_user(role=Role.TEAM_MEMBER, employee_name="Mention Target")
    meeting = make_meeting(owner, [mentioned])
    task = make_task(meeting, mentioned)

    comment = client.post(
        f"/api/tasks/{task.id}/comments",
        json={"message": f"Please review this @{mentioned.employee_name}"},
        headers=auth_header(owner),
    )
    assert comment.status_code == 201

    log = client.get("/api/activity-log", headers=auth_header(owner))
    actions = [entry["action"] for entry in log.json()]
    assert "COMMENT_POSTED" in actions
    assert "MEMBER_MENTIONED" in actions


def test_a_tasks_status_change_appears_in_the_activity_log(
    client, make_user, make_meeting, make_task, auth_header
):
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [assignee])
    task = make_task(meeting, assignee, status=TaskStatus.TODO)

    status_change = client.patch(
        f"/api/tasks/{task.id}/status",
        json={"status": "IN_PROGRESS"},
        headers=auth_header(assignee),
    )
    assert status_change.status_code == 200

    log = client.get("/api/activity-log", headers=auth_header(owner))
    entries = [e for e in log.json() if e["action"] == "TASK_STATUS_CHANGED"]
    assert len(entries) == 1
    assert entries[0]["actorId"] == assignee.id
    assert entries[0]["entityType"] == "Task"
    assert entries[0]["entityId"] == task.id


def test_reassigning_a_tasks_owner_appears_in_the_activity_log(
    client, make_user, make_meeting, make_task, auth_header
):
    owner, _ = make_user(role=Role.ADMIN)
    original_assignee, _ = make_user(role=Role.TEAM_MEMBER)
    new_assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [original_assignee, new_assignee])
    task = make_task(meeting, original_assignee)

    reassign = client.patch(
        f"/api/tasks/{task.id}",
        json={"assigneeId": new_assignee.id},
        headers=auth_header(owner),
    )
    assert reassign.status_code == 200

    log = client.get("/api/activity-log", headers=auth_header(owner))
    actions = [entry["action"] for entry in log.json()]
    assert "TASK_REASSIGNED" in actions
    # Reassignment also (re-)schedules the assignment email - AC2's "assigns a task"
    assert "NOTIFICATION_SENT" in actions


def test_deleting_a_task_directly_appears_in_the_activity_log(
    client, make_user, make_meeting, make_task, auth_header
):
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [assignee])
    task = make_task(meeting, assignee)

    delete = client.delete(f"/api/tasks/{task.id}", headers=auth_header(owner))
    assert delete.status_code == 204

    log = client.get("/api/activity-log", headers=auth_header(owner))
    entries = [e for e in log.json() if e["action"] == "TASK_DELETED"]
    assert len(entries) == 1
    assert entries[0]["entityId"] == task.id


def test_creating_a_task_schedules_a_notification_recorded_in_the_activity_log(
    client, make_user, make_meeting, auth_header
):
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [assignee])

    created = client.post(
        f"/api/meetings/{meeting.id}/tasks",
        json={"title": "Prep the deck", "assigneeId": assignee.id},
        headers=auth_header(owner),
    )
    assert created.status_code == 201

    log = client.get("/api/activity-log", headers=auth_header(owner))
    actions = [entry["action"] for entry in log.json()]
    assert "NOTIFICATION_SENT" in actions


def test_an_ado_reference_in_a_tasks_description_appears_in_the_activity_log(
    client, make_user, make_meeting, auth_header
):
    """AC2's "Azure DevOps references" coverage: an '@<number>' token in a
    Task's Description/Notes is detected even when Azure DevOps itself is
    unreachable/unconfigured (FR-033), since the Activity Log records that a
    reference was detected, independent of whether it later resolves."""
    owner, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(owner, [assignee])

    created = client.post(
        f"/api/meetings/{meeting.id}/tasks",
        json={
            "title": "Wire up the API",
            "assigneeId": assignee.id,
            "descriptionNotes": "See @1234 for the spec",
        },
        headers=auth_header(owner),
    )
    assert created.status_code == 201

    log = client.get("/api/activity-log", headers=auth_header(owner))
    entries = [e for e in log.json() if e["action"] == "ADO_REFERENCE_DETECTED"]
    assert len(entries) == 1
    assert entries[0]["actorId"] == owner.id
