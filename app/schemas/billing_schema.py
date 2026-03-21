from datetime import datetime

from pydantic import BaseModel


class CheckoutSessionRequest(BaseModel):
    price_key: str = "premium_monthly"
    success_path: str | None = None
    cancel_path: str | None = None


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class BillingPortalResponse(BaseModel):
    portal_url: str


class StripeWebhookAck(BaseModel):
    received: bool


class BillingStatusResponse(BaseModel):
    user_id: int
    subscription_tier: str
    subscription_status: str
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    subscription_expires_at: datetime | None = None
    trial_ends_at: datetime | None = None
    has_premium_access: bool
