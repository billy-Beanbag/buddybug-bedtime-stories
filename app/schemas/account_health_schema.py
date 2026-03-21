from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccountHealthSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    health_score: int
    health_band: str
    active_children_count: int
    stories_opened_30d: int
    stories_completed_30d: int
    saved_books_count: int
    support_tickets_open_count: int
    premium_status: str | None = None
    dormant_days: int | None = None
    snapshot_reasoning: str | None = None
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class AccountHealthSnapshotResponse(BaseModel):
    snapshot: AccountHealthSnapshotRead
    user_email: str
    user_display_name: str | None = None


class AccountHealthSummaryResponse(BaseModel):
    items: list[AccountHealthSnapshotResponse]
    total: int
