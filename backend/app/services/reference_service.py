from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.integrations.azure_devops_client import AzureDevOpsClient
from app.models.comment import MentionSourceType, TaskAdoReference
from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.ado_reference_repository import AdoReferenceRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.mention_parser import find_ado_ids, find_mention_tokens, resolve_mentions


def get_attendee_users(db: Session, meeting: Meeting) -> list[User]:
    user_repo = UserRepository(db)
    users = (user_repo.get_by_id(attendee.user_id) for attendee in meeting.attendees)
    return [user for user in users if user is not None]


def sync_task_content_references(
    db: Session,
    task_id: int,
    meeting_id: int,
    *texts: str | None,
    client: AzureDevOpsClient | None = None,
) -> None:
    """Re-derives the Task-sourced mentions and Linked Azure DevOps Items for a
    Task's own Title/Description-Notes whenever either is written (FR-028,
    FR-030) — independent of any Comment-sourced mentions/references on the
    same Task.
    """
    meeting = MeetingRepository(db).get_by_id(meeting_id)
    attendees = get_attendee_users(db, meeting) if meeting is not None else []

    mentioned_users = resolve_mentions(find_mention_tokens(*texts), attendees)
    CommentRepository(db).replace_mentions(
        MentionSourceType.TASK, task_id, [user.id for user in mentioned_users]
    )
    _sync_ado_references(db, task_id, find_ado_ids(*texts), client)


def sync_comment_references(
    db: Session, task_id: int, ado_ids: list[int], client: AzureDevOpsClient | None = None
) -> None:
    _sync_ado_references(db, task_id, ado_ids, client)


def list_task_references(
    db: Session, task_id: int, client: AzureDevOpsClient | None = None
) -> list[TaskAdoReference]:
    if TaskRepository(db).get_by_id(task_id) is None:
        raise NotFoundError("Task not found.")

    repo = AdoReferenceRepository(db)
    rows = repo.list_by_task(task_id)
    ado_client = client or AzureDevOpsClient()
    for row in rows:
        item = ado_client.get(row.ado_work_item_id)
        repo.upsert(
            task_id=task_id,
            ado_work_item_id=row.ado_work_item_id,
            cached_title=item.title if item else None,
            cached_type=item.type if item else None,
            is_available=item is not None,
        )
    return repo.list_by_task(task_id)


def _sync_ado_references(
    db: Session, task_id: int, ado_ids: list[int], client: AzureDevOpsClient | None
) -> None:
    if not ado_ids:
        return
    ado_client = client or AzureDevOpsClient()
    repo = AdoReferenceRepository(db)
    for ado_id in ado_ids:
        item = ado_client.get(ado_id)
        repo.upsert(
            task_id=task_id,
            ado_work_item_id=ado_id,
            cached_title=item.title if item else None,
            cached_type=item.type if item else None,
            is_available=item is not None,
        )
