from datetime import datetime

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLogEntry
from app.repositories.activity_log_repository import ActivityLogRepository


def log_activity(db: Session, actor_id: int, action: str, entity_type: str, entity_id: int) -> None:
    entry = ActivityLogEntry(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(entry)
    db.flush()


def list_activity_log(
    db: Session,
    entity_type: str | None,
    since: datetime | None,
    page: int,
    page_size: int,
) -> list[tuple[ActivityLogEntry, str]]:
    return ActivityLogRepository(db).list(entity_type, since, page, page_size)
