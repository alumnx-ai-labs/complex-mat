from datetime import date, time

from sqlalchemy import extract, select
from sqlalchemy.orm import Session, selectinload

from app.models.meeting import Meeting, MeetingAttendee


class MeetingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        title: str,
        meeting_date: date,
        meeting_time: time,
        agenda_notes: str | None,
        owner_id: int,
        attendee_ids: list[int],
    ) -> Meeting:
        meeting = Meeting(
            title=title,
            date=meeting_date,
            time=meeting_time,
            agenda_notes=agenda_notes,
            owner_id=owner_id,
        )
        self.db.add(meeting)
        self.db.flush()
        self.set_attendees(meeting, attendee_ids)
        self.db.flush()
        self.db.refresh(meeting)
        return meeting

    def set_attendees(self, meeting: Meeting, attendee_ids: list[int]) -> None:
        meeting.attendees = [
            MeetingAttendee(meeting_id=meeting.id, user_id=user_id) for user_id in attendee_ids
        ]

    def get_by_id(self, meeting_id: int) -> Meeting | None:
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(selectinload(Meeting.attendees))
        )
        return self.db.scalars(stmt).first()

    def list_for_admin(self, month: int | None, year: int | None) -> list[Meeting]:
        return self._list(None, month, year)

    def list_for_attendee(self, user_id: int, month: int | None, year: int | None) -> list[Meeting]:
        return self._list(user_id, month, year)

    def _list(self, attendee_user_id: int | None, month: int | None, year: int | None) -> list[Meeting]:
        stmt = select(Meeting).options(selectinload(Meeting.attendees))
        if attendee_user_id is not None:
            stmt = stmt.join(MeetingAttendee).where(MeetingAttendee.user_id == attendee_user_id)
        if month is not None:
            stmt = stmt.where(extract("month", Meeting.date) == month)
        if year is not None:
            stmt = stmt.where(extract("year", Meeting.date) == year)
        stmt = stmt.order_by(Meeting.date, Meeting.time)
        return list(self.db.scalars(stmt).unique().all())

    def is_attendee(self, meeting: Meeting, user_id: int) -> bool:
        return any(attendee.user_id == user_id for attendee in meeting.attendees)

    def delete(self, meeting: Meeting) -> None:
        self.db.delete(meeting)
        self.db.flush()
