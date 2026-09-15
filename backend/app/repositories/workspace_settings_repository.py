from sqlalchemy.orm import Session

from app.models.workspace_settings import WorkspaceSettings


class WorkspaceSettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_default_admin_id(self) -> int | None:
        settings = self.db.get(WorkspaceSettings, 1)
        return settings.default_admin_user_id if settings else None
