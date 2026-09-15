from datetime import date, time
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationFailedError
from app.models.meeting import Meeting, MeetingAttendee
from app.models.user import Role, User
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services import task_service
from app.services.activity_log_service import log_activity


def create_meeting(
    db: Session,
    owner: User,
    title: str,
    meeting_date: date,
    meeting_time: time,
    agenda_notes: str | None,
    attendee_ids: list[int],
) -> Meeting:
    user_repo = UserRepository(db)
    attendee_ids = list(dict.fromkeys(attendee_ids))
    for attendee_id in attendee_ids:
        attendee = user_repo.get_by_id(attendee_id)
        if attendee is None or not attendee.is_active:
            raise ValidationFailedError(f"Attendee {attendee_id} is not an active user.")
    if owner.id not in attendee_ids:
        attendee_ids.append(owner.id)

    meeting = MeetingRepository(db).create(
        title=title,
        meeting_date=meeting_date,
        meeting_time=meeting_time,
        agenda_notes=agenda_notes,
        owner_id=owner.id,
        attendee_ids=attendee_ids,
    )
    log_activity(db, owner.id, "MEETING_CREATED", "Meeting", meeting.id)
    return meeting


def list_meetings(
    db: Session, current_user: User, month: int | None, year: int | None
) -> list[Meeting]:
    repo = MeetingRepository(db)
    if current_user.role == Role.ADMIN:
        return repo.list_for_admin(month, year)
    return repo.list_for_attendee(current_user.id, month, year)


def get_meeting_detail(db: Session, current_user: User, meeting_id: int) -> Meeting:
    repo = MeetingRepository(db)
    meeting = repo.get_by_id(meeting_id)
    if meeting is None:
        raise NotFoundError("Meeting not found.")
    if current_user.role != Role.ADMIN and not repo.is_attendee(meeting, current_user.id):
        raise ForbiddenError("You are not an Attendee of this Meeting.")
    return meeting


def _get_meeting_or_404(db: Session, meeting_id: int) -> Meeting:
    meeting = MeetingRepository(db).get_by_id(meeting_id)
    if meeting is None:
        raise NotFoundError("Meeting not found.")
    return meeting


def update_meeting(db: Session, admin: User, meeting_id: int, fields: dict[str, Any]) -> Meeting:
    meeting = _get_meeting_or_404(db, meeting_id)
    user_repo = UserRepository(db)

    for key in ("title", "date", "time", "agenda_notes"):
        if key in fields:
            setattr(meeting, key, fields[key])

    if "attendee_ids" in fields:
        attendee_ids = list(dict.fromkeys(fields["attendee_ids"]))
        for attendee_id in attendee_ids:
            attendee = user_repo.get_by_id(attendee_id)
            if attendee is None or not attendee.is_active:
                raise ValidationFailedError(f"Attendee {attendee_id} is not an active user.")
        if meeting.owner_id not in attendee_ids:
            attendee_ids.append(meeting.owner_id)

        previous_attendee_ids = {attendee.user_id for attendee in meeting.attendees}
        new_attendee_ids = set(attendee_ids)
        removed_ids = previous_attendee_ids - new_attendee_ids
        added_ids = new_attendee_ids - previous_attendee_ids

        meeting.attendees = [
            attendee for attendee in meeting.attendees if attendee.user_id not in removed_ids
        ] + [MeetingAttendee(meeting_id=meeting.id, user_id=uid) for uid in added_ids]

        if removed_ids:
            task_repo = TaskRepository(db)
            for task in task_repo.list_by_meeting(meeting.id):
                if task.assignee_id in removed_ids:
                    task_repo.update(task, needs_reassignment=True)

    db.flush()
    db.refresh(meeting)
    log_activity(db, admin.id, "MEETING_UPDATED", "Meeting", meeting.id)
    return meeting


def delete_meeting(db: Session, admin: User, meeting_id: int) -> None:
    meeting = _get_meeting_or_404(db, meeting_id)
    task_service.delete_tasks_for_meeting(db, meeting.id)
    MeetingRepository(db).delete(meeting)
    log_activity(db, admin.id, "MEETING_DELETED", "Meeting", meeting_id)
