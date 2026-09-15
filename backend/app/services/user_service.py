from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import Role, User
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_settings_repository import WorkspaceSettingsRepository
from app.services.activity_log_service import log_activity


def search_users(db: Session, q: str | None, active_only: bool) -> list[User]:
    return UserRepository(db).search(q, active_only)


def create_member(
    db: Session,
    admin: User,
    employee_name: str,
    employee_mail_id: str,
    employee_id: str,
    password: str,
    role: Role,
) -> User:
    repo = UserRepository(db)
    if repo.get_by_mail_id(employee_mail_id) is not None:
        raise ConflictError("That Employee Mail ID is already registered to another member.")
    if repo.get_by_employee_id(employee_id) is not None:
        raise ConflictError("That Employee ID is already registered to another member.")

    user = repo.create(
        employee_name=employee_name,
        employee_mail_id=employee_mail_id,
        employee_id=employee_id,
        password_hash=hash_password(password),
        role=role,
    )
    log_activity(db, admin.id, "MEMBER_ADDED", "User", user.id)
    return user


def update_role(db: Session, admin: User, user_id: int, role: Role) -> User:
    user = _get_user_or_404(db, user_id)
    user = UserRepository(db).update_role(user, role)
    log_activity(db, admin.id, "MEMBER_ROLE_CHANGED", "User", user.id)
    return user


def reset_password(db: Session, admin: User, user_id: int, password: str) -> User:
    user = _get_user_or_404(db, user_id)
    user = UserRepository(db).update_password_hash(user, hash_password(password))
    log_activity(db, admin.id, "MEMBER_PASSWORD_RESET", "User", user.id)
    return user


def set_active(db: Session, admin: User, user_id: int, is_active: bool) -> User:
    user = _get_user_or_404(db, user_id)
    user = UserRepository(db).set_active(user, is_active)

    if is_active:
        log_activity(db, admin.id, "MEMBER_REACTIVATED", "User", user.id)
    else:
        _transfer_owned_meetings(db, user)
        _flag_assigned_tasks_for_reassignment(db, user)
        log_activity(db, admin.id, "MEMBER_DEACTIVATED", "User", user.id)

    return user


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise NotFoundError("User not found.")
    return user


def _transfer_owned_meetings(db: Session, user: User) -> None:
    owned_meetings = MeetingRepository(db).list_owned_by(user.id)
    if not owned_meetings:
        return
    default_admin_id = WorkspaceSettingsRepository(db).get_default_admin_id()
    if default_admin_id is None:
        return
    for meeting in owned_meetings:
        meeting.owner_id = default_admin_id
    db.flush()


def _flag_assigned_tasks_for_reassignment(db: Session, user: User) -> None:
    task_repo = TaskRepository(db)
    for task, _meeting_title in task_repo.list_by_assignee(user.id):
        task_repo.update(task, needs_reassignment=True)
