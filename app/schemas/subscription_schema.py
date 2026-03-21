from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    subscription_tier: str
    subscription_status: str
    subscription_expires_at: datetime | None = None
    trial_ends_at: datetime | None = None
    has_premium_access: bool
    is_trial_active: bool
    is_subscription_active: bool


class SubscriptionAdminUpdate(BaseModel):
    subscription_tier: str | None = None
    subscription_status: str | None = None
    subscription_expires_at: datetime | None = None
    trial_ends_at: datetime | None = None


class ReaderAccessResponse(BaseModel):
    book_id: int
    can_read_full_book: bool
    can_use_audio: bool
    preview_page_limit: int = Field(default=2, ge=0)
    reason: str
