from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import require_role
from app.models.user import Role, User
from app.schemas.activity_log import ActivityLogEntryResponse
from app.services import activity_log_service

router = APIRouter(prefix="/api/activity-log", tags=["activity-log"])


@router.get("", response_model=list[ActivityLogEntryResponse])
def list_activity_log(
    entity_type: str | None = Query(default=None, alias="entityType"),
    since: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200, alias="pageSize"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(Role.ADMIN)),
) -> list[ActivityLogEntryResponse]:
    rows = activity_log_service.list_activity_log(db, entity_type, since, page, page_size)
    return [
        ActivityLogEntryResponse(
            id=entry.id,
            actor_id=entry.actor_id,
            actor_name=actor_name,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            timestamp=entry.timestamp,
        )
        for entry, actor_name in rows
    ]
