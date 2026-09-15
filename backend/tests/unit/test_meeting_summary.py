from app.api.meetings import _to_summary
from app.models.user import Role


def test_to_summary_reports_zero_tasks_for_a_meeting_with_none(db_session, make_user, make_meeting):
    admin, _ = make_user(role=Role.ADMIN)
    meeting = make_meeting(admin, [])

    summary = _to_summary(db_session, meeting)

    assert summary.task_count == 0


def test_to_summary_counts_all_tasks_on_the_meeting(
    db_session, make_user, make_meeting, make_task
):
    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(admin, [assignee])
    make_task(meeting, assignee)
    make_task(meeting, assignee)
    make_task(meeting, assignee)

    summary = _to_summary(db_session, meeting)

    assert summary.task_count == 3


def test_to_summary_reflects_deletions_live(db_session, make_user, make_meeting, make_task):
    from app.repositories.task_repository import TaskRepository

    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting = make_meeting(admin, [assignee])
    task_one = make_task(meeting, assignee)
    make_task(meeting, assignee)
    assert _to_summary(db_session, meeting).task_count == 2

    TaskRepository(db_session).delete(task_one)

    assert _to_summary(db_session, meeting).task_count == 1


def test_to_summary_only_counts_tasks_on_this_meeting(
    db_session, make_user, make_meeting, make_task
):
    admin, _ = make_user(role=Role.ADMIN)
    assignee, _ = make_user(role=Role.TEAM_MEMBER)
    meeting_a = make_meeting(admin, [assignee])
    meeting_b = make_meeting(admin, [assignee])
    make_task(meeting_a, assignee)
    make_task(meeting_b, assignee)
    make_task(meeting_b, assignee)

    assert _to_summary(db_session, meeting_a).task_count == 1
    assert _to_summary(db_session, meeting_b).task_count == 2


def test_to_summary_includes_owner_name(db_session, make_user, make_meeting):
    admin, _ = make_user(role=Role.ADMIN)
    meeting = make_meeting(admin, [])

    summary = _to_summary(db_session, meeting)

    assert summary.owner_id == admin.id
    assert summary.owner_name == admin.employee_name
