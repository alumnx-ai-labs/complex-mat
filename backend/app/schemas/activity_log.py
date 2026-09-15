from datetime import datetime

from app.schemas.camel import CamelModel


class ActivityLogEntryResponse(CamelModel):
    id: int
    actor_id: int
    actor_name: str
    action: str
    entity_type: str
    entity_id: int
    timestamp: datetime
