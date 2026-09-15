from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import TaskAdoReference


class AdoReferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, task_id: int, ado_work_item_id: int) -> TaskAdoReference | None:
        stmt = select(TaskAdoReference).where(
            TaskAdoReference.task_id == task_id,
            TaskAdoReference.ado_work_item_id == ado_work_item_id,
        )
        return self.db.scalars(stmt).first()

    def list_by_task(self, task_id: int) -> list[TaskAdoReference]:
        stmt = (
            select(TaskAdoReference)
            .where(TaskAdoReference.task_id == task_id)
            .order_by(TaskAdoReference.ado_work_item_id)
        )
        return list(self.db.scalars(stmt).all())

    def upsert(
        self,
        task_id: int,
        ado_work_item_id: int,
        cached_title: str | None,
        cached_type: str | None,
        is_available: bool,
    ) -> TaskAdoReference:
        row = self.get(task_id, ado_work_item_id)
        if row is None:
            row = TaskAdoReference(task_id=task_id, ado_work_item_id=ado_work_item_id)
            self.db.add(row)
        if cached_title is not None:
            row.cached_title = cached_title
        if cached_type is not None:
            row.cached_type = cached_type
        row.is_available = is_available
        row.last_checked_at = datetime.now(timezone.utc)
        self.db.flush()
        self.db.refresh(row)
        return row
