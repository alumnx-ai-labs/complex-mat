from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment, CommentMention, MentionSourceType


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, task_id: int, author_id: int, message: str) -> Comment:
        comment = Comment(task_id=task_id, author_id=author_id, message=message)
        self.db.add(comment)
        self.db.flush()
        self.db.refresh(comment)
        return comment

    def list_by_task(self, task_id: int) -> list[Comment]:
        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        return list(self.db.scalars(stmt).all())

    def delete(self, comment: Comment) -> None:
        self.db.delete(comment)
        self.db.flush()

    def add_mentions(
        self, source_type: MentionSourceType, source_id: int, user_ids: list[int]
    ) -> list[CommentMention]:
        mentions = [
            CommentMention(source_type=source_type, source_id=source_id, mentioned_user_id=uid)
            for uid in user_ids
        ]
        for mention in mentions:
            self.db.add(mention)
        self.db.flush()
        return mentions

    def list_mentions(
        self, source_type: MentionSourceType, source_id: int
    ) -> list[CommentMention]:
        stmt = select(CommentMention).where(
            CommentMention.source_type == source_type, CommentMention.source_id == source_id
        )
        return list(self.db.scalars(stmt).all())

    def replace_mentions(
        self, source_type: MentionSourceType, source_id: int, user_ids: list[int]
    ) -> None:
        for row in self.list_mentions(source_type, source_id):
            self.db.delete(row)
        self.db.flush()
        self.add_mentions(source_type, source_id, user_ids)
