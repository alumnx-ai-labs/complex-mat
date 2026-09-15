import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MentionSourceType(str, enum.Enum):
    TASK = "TASK"
    COMMENT = "COMMENT"


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CommentMention(Base):
    __tablename__ = "comment_mentions"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[MentionSourceType] = mapped_column(Enum(MentionSourceType), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    mentioned_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class TaskAdoReference(Base):
    __tablename__ = "task_ado_references"
    __table_args__ = (
        UniqueConstraint("task_id", "ado_work_item_id", name="uq_task_ado_reference"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    ado_work_item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cached_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cached_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
