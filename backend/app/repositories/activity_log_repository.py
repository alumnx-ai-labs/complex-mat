from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLogEntry
from app.models.user import User


class ActivityLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        entity_type: str | None = None,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[tuple[ActivityLogEntry, str]]:
        stmt = select(ActivityLogEntry, User.employee_name).join(
            User, User.id == ActivityLogEntry.actor_id
        )
        if entity_type:
            stmt = stmt.where(ActivityLogEntry.entity_type == entity_type)
        if since:
            stmt = stmt.where(ActivityLogEntry.timestamp >= since)
        stmt = (
            # id DESC breaks ties when two entries land in the same timestamp
            # tick (the OS clock's resolution is coarser than back-to-back
            # log_activity calls can be).
            stmt.order_by(ActivityLogEntry.timestamp.desc(), ActivityLogEntry.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [(entry, actor_name) for entry, actor_name in self.db.execute(stmt).all()]
