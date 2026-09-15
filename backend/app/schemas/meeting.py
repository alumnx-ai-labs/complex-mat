import datetime
from datetime import date, time

from app.schemas.camel import CamelModel
from app.schemas.task import TaskResponse


class MeetingCreateRequest(CamelModel):
    title: str
    date: date
    time: time
    agenda_notes: str | None = None
    attendee_ids: list[int]


class MeetingUpdateRequest(CamelModel):
    title: str | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None
    agenda_notes: str | None = None
    attendee_ids: list[int] | None = None


class AttendeeResponse(CamelModel):
    id: int
    employee_name: str

    model_config = CamelModel.model_config | {"from_attributes": True}


class MeetingSummaryResponse(CamelModel):
    id: int
    title: str
    date: date
    time: time
    owner_id: int
    owner_name: str
    task_count: int

    model_config = CamelModel.model_config | {"from_attributes": True}


class MeetingDetailResponse(CamelModel):
    id: int
    title: str
    date: date
    time: time
    agenda_notes: str | None
    owner_id: int
    owner_name: str
    attendees: list[AttendeeResponse]
    tasks: list[TaskResponse] = []

    model_config = CamelModel.model_config | {"from_attributes": True}
