from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.tasks import task_to_response
from app.db.session import get_db
from app.deps.auth import get_current_user, require_role
from app.models.meeting import Meeting
from app.models.user import Role, User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.meeting import (
    AttendeeResponse,
    MeetingCreateRequest,
    MeetingDetailResponse,
    MeetingSummaryResponse,
    MeetingUpdateRequest,
)
from app.services import meeting_service

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


def _to_summary(db: Session, meeting: Meeting) -> MeetingSummaryResponse:
    owner = UserRepository(db).get_by_id(meeting.owner_id)
    return MeetingSummaryResponse(
        id=meeting.id,
        title=meeting.title,
        date=meeting.date,
        time=meeting.time,
        owner_id=meeting.owner_id,
        owner_name=owner.employee_name if owner else "",
        task_count=0,
    )


def _to_detail(db: Session, meeting: Meeting) -> MeetingDetailResponse:
    user_repo = UserRepository(db)
    owner = user_repo.get_by_id(meeting.owner_id)
    attendees = [
        AttendeeResponse(id=user.id, employee_name=user.employee_name)
        for user in (
            user_repo.get_by_id(attendee.user_id) for attendee in meeting.attendees
        )
        if user is not None
    ]
    tasks = [
        task_to_response(db, task) for task in TaskRepository(db).list_by_meeting(meeting.id)
    ]
    return MeetingDetailResponse(
        id=meeting.id,
        title=meeting.title,
        date=meeting.date,
        time=meeting.time,
        agenda_notes=meeting.agenda_notes,
        owner_id=meeting.owner_id,
        owner_name=owner.employee_name if owner else "",
        attendees=attendees,
        tasks=tasks,
    )


@router.post("", response_model=MeetingSummaryResponse, status_code=201)
def create_meeting(
    payload: MeetingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> MeetingSummaryResponse:
    meeting = meeting_service.create_meeting(
        db,
        owner=current_user,
        title=payload.title,
        meeting_date=payload.date,
        meeting_time=payload.time,
        agenda_notes=payload.agenda_notes,
        attendee_ids=payload.attendee_ids,
    )
    return _to_summary(db, meeting)


@router.get("", response_model=list[MeetingSummaryResponse])
def list_meetings(
    month: int | None = Query(default=None),
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MeetingSummaryResponse]:
    meetings = meeting_service.list_meetings(db, current_user, month, year)
    return [_to_summary(db, meeting) for meeting in meetings]


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting_detail(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingDetailResponse:
    meeting = meeting_service.get_meeting_detail(db, current_user, meeting_id)
    return _to_detail(db, meeting)


@router.patch("/{meeting_id}", response_model=MeetingDetailResponse)
def update_meeting(
    meeting_id: int,
    payload: MeetingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> MeetingDetailResponse:
    fields = payload.model_dump(exclude_unset=True)
    meeting = meeting_service.update_meeting(db, current_user, meeting_id, fields)
    return _to_detail(db, meeting)


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> None:
    meeting_service.delete_meeting(db, current_user, meeting_id)
