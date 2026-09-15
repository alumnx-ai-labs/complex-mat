from datetime import datetime

from app.schemas.camel import CamelModel


class CommentMentionResponse(CamelModel):
    user_id: int
    employee_name: str


class CommentAdoReferenceResponse(CamelModel):
    ado_work_item_id: int
    title: str | None
    type: str | None
    is_available: bool


class CommentCreateRequest(CamelModel):
    message: str


class CommentResponse(CamelModel):
    id: int
    task_id: int
    author_id: int
    author_name: str
    message: str
    mentions: list[CommentMentionResponse]
    ado_references: list[CommentAdoReferenceResponse]
    created_at: datetime
