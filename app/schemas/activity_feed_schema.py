from datetime import datetime

from pydantic import BaseModel


class ActivityFeedItem(BaseModel):
    timestamp: datetime
    event_type: str
    entity_type: str
    entity_id: str | None = None
    summary: str
    actor_user_id: int | None = None
    actor_email: str | None = None
    source_table: str
    metadata_json: str | None = None


class ActivityFeedResponse(BaseModel):
    items: list[ActivityFeedItem]
