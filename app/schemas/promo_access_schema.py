from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PromoAccessCodeCreate(BaseModel):
    key: str
    name: str
    code: str
    partner_name: str | None = None
    access_type: str
    subscription_tier_granted: str | None = None
    duration_days: int | None = None
    max_redemptions: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True


class PromoAccessCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    code: str
    partner_name: str | None = None
    access_type: str
    subscription_tier_granted: str | None = None
    duration_days: int | None = None
    max_redemptions: int | None = None
    redemption_count: int
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PromoAccessCodeUpdate(BaseModel):
    key: str | None = None
    name: str | None = None
    code: str | None = None
    partner_name: str | None = None
    access_type: str | None = None
    subscription_tier_granted: str | None = None
    duration_days: int | None = None
    max_redemptions: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None


class PromoAccessRedeemRequest(BaseModel):
    code: str


class PromoAccessRedemptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    promo_access_code_id: int
    user_id: int
    redeemed_at: datetime
    expires_at: datetime | None = None
    created_at: datetime


class PromoAccessRedeemResponse(BaseModel):
    code: PromoAccessCodeRead
    redemption: PromoAccessRedemptionRead
    subscription_status: str
    subscription_tier: str
    expires_at: datetime | None = None
