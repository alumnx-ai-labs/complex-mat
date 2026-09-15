from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationFailedError
from app.integrations.azure_devops_client import AzureDevOpsClient
from app.models.comment import Comment, MentionSourceType
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.user import Role, User
from app.repositories.comment_repository import CommentRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.task_repository import TaskRepository
from app.services.activity_log_service import log_activity
from app.services.mention_parser import find_ado_ids, find_mention_tokens, resolve_mentions
from app.services.reference_service import get_attendee_users, sync_comment_references


def _get_task_and_meeting(db: Session, task_id: int) -> tuple[Task, Meeting]:
    task = TaskRepository(db).get_by_id(task_id)
    if task is None:
        raise NotFoundError("Task not found.")
    meeting = MeetingRepository(db).get_by_id(task.meeting_id)
    if meeting is None:
        raise NotFoundError("Meeting not found.")
    return task, meeting


def _can_comment(current_user: User, task: Task, meeting: Meeting) -> bool:
    return (
        current_user.id == meeting.owner_id
        or current_user.id == task.assignee_id
        or current_user.role == Role.ADMIN
    )


def list_comments(db: Session, task_id: int) -> list[Comment]:
    _get_task_and_meeting(db, task_id)
    return CommentRepository(db).list_by_task(task_id)


def create_comment(
    db: Session,
    current_user: User,
    task_id: int,
    message: str,
    client: AzureDevOpsClient | None = None,
) -> Comment:
    task, meeting = _get_task_and_meeting(db, task_id)
    if not _can_comment(current_user, task, meeting):
        raise ForbiddenError(
            "Only the Meeting Owner, the Task's Assignee, or an Admin may comment on this Task."
        )
    if not message or not message.strip():
        raise ValidationFailedError("Comment message is required.")

    comment_repo = CommentRepository(db)
    comment = comment_repo.create(
        task_id=task_id, author_id=current_user.id, message=message.strip()
    )
    log_activity(db, current_user.id, "COMMENT_POSTED", "Task", task_id)

    attendees = get_attendee_users(db, meeting)
    mentioned_users = resolve_mentions(find_mention_tokens(comment.message), attendees)
    comment_repo.add_mentions(
        MentionSourceType.COMMENT, comment.id, [user.id for user in mentioned_users]
    )
    for user in mentioned_users:
        log_activity(db, current_user.id, "MEMBER_MENTIONED", "User", user.id)

    sync_comment_references(
        db, task_id, find_ado_ids(comment.message), client, actor_id=current_user.id
    )

    return comment


def search_mention_candidates(db: Session, meeting_id: int, q: str | None) -> list[User]:
    meeting = MeetingRepository(db).get_by_id(meeting_id)
    if meeting is None:
        raise NotFoundError("Meeting not found.")
    attendees = get_attendee_users(db, meeting)
    if not q:
        return attendees
    lowered = q.lower()
    return [user for user in attendees if lowered in user.employee_name.lower()]
