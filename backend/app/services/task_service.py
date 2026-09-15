from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationFailedError
from app.models.meeting import Meeting
from app.models.task import Task, TaskStatus
from app.models.user import Role, User
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.task_repository import TaskRepository
from app.services.reference_service import sync_task_content_references


def _get_meeting_or_404(db: Session, meeting_id: int) -> Meeting:
    meeting = MeetingRepository(db).get_by_id(meeting_id)
    if meeting is None:
        raise NotFoundError("Meeting not found.")
    return meeting


def _get_task_or_404(db: Session, task_id: int) -> Task:
    task = TaskRepository(db).get_by_id(task_id)
    if task is None:
        raise NotFoundError("Task not found.")
    return task


def _validate_assignee(db: Session, meeting: Meeting, assignee_id: int) -> None:
    if not MeetingRepository(db).is_attendee(meeting, assignee_id):
        raise ValidationFailedError("Assignee must be an Attendee of this Meeting.")


def create_task(
    db: Session,
    owner: User,
    meeting_id: int,
    title: str,
    assignee_id: int,
    description_notes: str | None,
    due_date: date | None,
) -> Task:
    meeting = _get_meeting_or_404(db, meeting_id)
    if owner.id != meeting.owner_id:
        raise ForbiddenError("Only the Meeting Owner may assign a Task's Assignee.")
    _validate_assignee(db, meeting, assignee_id)
    task = TaskRepository(db).create(
        meeting_id=meeting.id,
        title=title,
        assignee_id=assignee_id,
        description_notes=description_notes,
        due_date=due_date,
    )
    sync_task_content_references(db, task.id, meeting.id, task.title, task.description_notes)
    return task


def list_my_tasks(db: Session, current_user: User) -> list[tuple[Task, str]]:
    return TaskRepository(db).list_by_assignee(current_user.id)


def update_task_status(
    db: Session, current_user: User, task_id: int, status: TaskStatus
) -> Task:
    task = _get_task_or_404(db, task_id)
    if task.assignee_id != current_user.id:
        raise ForbiddenError("Only this task's Assignee may change its status.")
    return TaskRepository(db).update_status(task, status)


def update_task_description(
    db: Session, current_user: User, task_id: int, description_notes: str | None
) -> Task:
    task = _get_task_or_404(db, task_id)
    if task.assignee_id != current_user.id:
        raise ForbiddenError("Only this task's Assignee may edit its Description/Notes.")
    task = TaskRepository(db).update_description_notes(task, description_notes)
    sync_task_content_references(db, task.id, task.meeting_id, task.title, task.description_notes)
    return task


def update_task(db: Session, current_user: User, task_id: int, fields: dict[str, Any]) -> Task:
    task = _get_task_or_404(db, task_id)
    meeting = _get_meeting_or_404(db, task.meeting_id)
    is_owner = current_user.id == meeting.owner_id
    is_admin = current_user.role == Role.ADMIN
    is_assignee = current_user.id == task.assignee_id

    if is_owner:
        allowed = {"title", "due_date", "assignee_id"}
    elif is_admin:
        allowed = {"title", "due_date"}
    elif is_assignee:
        allowed = {"description_notes"}
    else:
        raise ForbiddenError("You do not have access to this Task.")

    disallowed = set(fields) - allowed
    if disallowed:
        raise ForbiddenError(f"You are not permitted to change: {', '.join(sorted(disallowed))}.")
    if "assignee_id" in fields:
        _validate_assignee(db, meeting, fields["assignee_id"])
    task = TaskRepository(db).update(task, **fields)
    if "title" in fields or "description_notes" in fields:
        sync_task_content_references(
            db, task.id, task.meeting_id, task.title, task.description_notes
        )
    return task


def delete_task(db: Session, current_user: User, task_id: int) -> None:
    task = _get_task_or_404(db, task_id)
    meeting = _get_meeting_or_404(db, task.meeting_id)
    if current_user.id != meeting.owner_id and current_user.role != Role.ADMIN:
        raise ForbiddenError("Only the Meeting Owner or an Admin may delete a Task.")
    TaskRepository(db).delete(task)
