from datetime import date, time

import pytest

from app.core.exceptions import NotFoundError, ValidationFailedError
from app.models.activity_log import ActivityLogEntry
from app.models.comment import MentionSourceType
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.user import Role
from app.repositories.ado_reference_repository import AdoReferenceRepository
from app.repositories.comment_repository import CommentRepository
from app.services import meeting_service


def test_update_meeting_updates_basic_fields(db_session, make_user, make_meeting):
    admin, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    meeting = make_meeting(admin, [])

    updated = meeting_service.update_meeting(
        db_session,
        other_admin,
        meeting.id,
        {"title": "New Title", "date": date(2026, 10, 1), "time": time(9, 0), "agenda_notes": "notes"},
    )

    assert updated.title == "New Title"
    assert updated.date == date(2026, 10, 1)
    assert updated.time == time(9, 0)
    assert updated.agenda_notes == "notes"


def test_update_meeting_ignores_owner_id_even_if_present_in_fields(db_session, make_user, make_meeting):
    admin, _ = make_user(role=Role.ADMIN)
    other_admin, _ = make_user(role=Role.ADMIN)
    meeting = make_meeting(admin, [])

    updated = meeting_service.update_meeting(
        db_session, other_admin, meeting.id, {"title": "x", "owner_id": other_admin.id}
    )

    assert updated.owner_id == admin.id


def test_update_meeting_raises_not_found_for_unknown_meeting(db_session, make_user):
    admin, _ = make_user(role=Role.ADMIN)

    with pytest.raises(NotFoundError):
        meeting_service.update_meeting(db_session, admin, 999999, {"title": "x"})


def test_update_meeting_rejects_an_inactive_attendee(db_session, make_user, make_meeting):
    admin, _ = make_user(role=Role.ADMIN)
    inactive, _ = make_user(role=Role.TEAM_MEMBER, is_active=False)
    meeting = make_meeting(admin, [])

    with pytest.raises(ValidationFailedError):
        meeting_service.update_meeting(db_session, admin, meeting.id, {"attendee_ids": [inactive.id]})


def test_update_meeting_flags_needs_reassignment_when_assignee_removed(
    db_session, make_user, make_meeting, make_task
):
    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(admin, [assignee])
    task = make_task(meeting, assignee)

    meeting_service.update_meeting(db_session, admin, meeting.id, {"attendee_ids": []})

    db_session.refresh(task)
    assert task.needs_reassignment is True
    assert task.assignee_id == assignee.id


def test_update_meeting_leaves_needs_reassignment_false_when_assignee_stays(
    db_session, make_user, make_meeting, make_task
):
    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(admin, [assignee])
    task = make_task(meeting, assignee)

    meeting_service.update_meeting(db_session, admin, meeting.id, {"title": "Renamed"})

    db_session.refresh(task)
    assert task.needs_reassignment is False


def test_update_meeting_attendee_diff_adds_removes_and_keeps_correctly(
    db_session, make_user, make_meeting
):
    admin, _ = make_user(role=Role.ADMIN)
    keep, _ = make_user(role=Role.TEAM_MEMBER)
    remove, _ = make_user(role=Role.TEAM_MEMBER)
    add, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(admin, [keep, remove])

    updated = meeting_service.update_meeting(
        db_session, admin, meeting.id, {"attendee_ids": [keep.id, add.id]}
    )

    attendee_ids = {attendee.user_id for attendee in updated.attendees}
    assert attendee_ids == {admin.id, keep.id, add.id}


def test_delete_meeting_removes_meeting_and_logs_a_single_activity_entry(
    db_session, make_user, make_meeting
):
    admin, _ = make_user(role=Role.ADMIN)
    meeting = make_meeting(admin, [])
    meeting_id = meeting.id

    meeting_service.delete_meeting(db_session, admin, meeting_id)

    assert db_session.get(Meeting, meeting_id) is None
    entries = [
        entry
        for entry in db_session.query(ActivityLogEntry).all()
        if entry.entity_type == "Meeting"
        and entry.entity_id == meeting_id
        and entry.action == "MEETING_DELETED"
    ]
    assert len(entries) == 1


def test_delete_meeting_raises_not_found_for_unknown_meeting(db_session, make_user):
    admin, _ = make_user(role=Role.ADMIN)

    with pytest.raises(NotFoundError):
        meeting_service.delete_meeting(db_session, admin, 999999)


def test_delete_meeting_cascades_tasks_comments_mentions_and_ado_references(
    db_session, make_user, make_meeting, make_task
):
    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(admin, [assignee])
    task = make_task(meeting, assignee)
    task_id = task.id

    comment_repo = CommentRepository(db_session)
    comment = comment_repo.create(task_id=task.id, author_id=admin.id, message="hello")
    comment_repo.add_mentions(MentionSourceType.COMMENT, comment.id, [assignee.id])
    comment_repo.add_mentions(MentionSourceType.TASK, task.id, [assignee.id])
    AdoReferenceRepository(db_session).upsert(task.id, 1234, "Some title", "Story", True)
    db_session.commit()

    meeting_service.delete_meeting(db_session, admin, meeting.id)

    assert db_session.get(Task, task_id) is None
    assert comment_repo.list_by_task(task_id) == []
    assert comment_repo.list_mentions(MentionSourceType.COMMENT, comment.id) == []
    assert comment_repo.list_mentions(MentionSourceType.TASK, task_id) == []
    assert AdoReferenceRepository(db_session).list_by_task(task_id) == []


def test_delete_meeting_does_not_touch_another_meetings_tasks(
    db_session, make_user, make_meeting, make_task
):
    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_a = make_meeting(admin, [assignee])
    meeting_b = make_meeting(admin, [assignee])
    task_a = make_task(meeting_a, assignee)
    task_b = make_task(meeting_b, assignee)

    meeting_service.delete_meeting(db_session, admin, meeting_a.id)

    assert db_session.get(Task, task_a.id) is None
    assert db_session.get(Task, task_b.id) is not None
