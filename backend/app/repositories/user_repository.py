from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_mail_id(self, employee_mail_id: str) -> User | None:
        stmt = select(User).where(User.employee_mail_id == employee_mail_id)
        return self.db.scalars(stmt).first()

    def search(self, q: str | None, active_only: bool = True) -> list[User]:
        stmt = select(User)
        if active_only:
            stmt = stmt.where(User.is_active.is_(True))
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                User.employee_name.ilike(pattern) | User.employee_id.ilike(pattern)
            )
        stmt = stmt.order_by(User.employee_name)
        return list(self.db.scalars(stmt).all())

    def mark_terms_accepted(self, user: User) -> User:
        user.terms_accepted = True
        self.db.flush()
        self.db.refresh(user)
        return user
