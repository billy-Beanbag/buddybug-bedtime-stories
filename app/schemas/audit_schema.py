from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int | None = None
    actor_email: str | None = None
    action_type: str
    entity_type: str
    entity_id: str | None = None
    summary: str
    metadata_json: str | None = None
    request_id: str | None = None
    created_at: datetime
