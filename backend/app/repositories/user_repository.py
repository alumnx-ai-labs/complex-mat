from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import Role, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_mail_id(self, employee_mail_id: str) -> User | None:
        stmt = select(User).where(User.employee_mail_id == employee_mail_id)
        return self.db.scalars(stmt).first()

    def get_by_employee_id(self, employee_id: str) -> User | None:
        stmt = select(User).where(User.employee_id == employee_id)
        return self.db.scalars(stmt).first()

    def create(
        self,
        employee_name: str,
        employee_mail_id: str,
        employee_id: str,
        password_hash: str,
        role: Role,
    ) -> User:
        user = User(
            employee_name=employee_name,
            employee_mail_id=employee_mail_id,
            employee_id=employee_id,
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def update_role(self, user: User, role: Role) -> User:
        user.role = role
        self.db.flush()
        self.db.refresh(user)
        return user

    def update_password_hash(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        self.db.flush()
        self.db.refresh(user)
        return user

    def set_active(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        self.db.flush()
        self.db.refresh(user)
        return user

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
