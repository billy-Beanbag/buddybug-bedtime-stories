from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReferralCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    code: str
    is_active: bool
    total_uses: int
    created_at: datetime
    updated_at: datetime


class ReferralAttributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    referrer_user_id: int
    referred_user_id: int
    referral_code_id: int
    signup_attributed_at: datetime
    premium_converted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class GiftSubscriptionCreate(BaseModel):
    duration_days: int = Field(ge=1)
    notes: str | None = None


class GiftSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchaser_user_id: int
    recipient_user_id: int | None
    code: str
    duration_days: int
    status: str
    purchased_at: datetime
    redeemed_at: datetime | None
    expires_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class GiftSubscriptionRedeemRequest(BaseModel):
    code: str


class GiftSubscriptionRedeemResponse(BaseModel):
    gift: GiftSubscriptionRead
    subscription_status: str
    subscription_tier: str
    expires_at: datetime | None


class ReferralSummaryResponse(BaseModel):
    referral_code: ReferralCodeRead | None
    total_referrals: int
    premium_conversions: int
