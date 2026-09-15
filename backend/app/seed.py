from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.activity_log import ActivityLogEntry  # noqa: F401
from app.models.comment import Comment, CommentMention, TaskAdoReference  # noqa: F401
from app.models.meeting import Meeting, MeetingAttendee  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.user import Role, User
from app.models.workspace_settings import WorkspaceSettings
from app.repositories.user_repository import UserRepository


def seed() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        admin = repo.get_by_mail_id(settings.default_admin_mail_id)
        if admin is None:
            admin = User(
                employee_name=settings.default_admin_employee_name,
                employee_mail_id=settings.default_admin_mail_id,
                employee_id=settings.default_admin_employee_id,
                password_hash=hash_password(settings.default_admin_password),
                role=Role.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.flush()
            print(f"Created default Admin: {admin.employee_mail_id}")
        else:
            print(f"Default Admin already exists: {admin.employee_mail_id}")

        workspace_settings = db.get(WorkspaceSettings, 1)
        if workspace_settings is None:
            db.add(WorkspaceSettings(id=1, default_admin_user_id=admin.id))
            print("Configured WorkspaceSettings.default_admin_user_id")
        else:
            workspace_settings.default_admin_user_id = admin.id

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
