from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BillingRecoveryCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    source_type: str
    external_reference: str | None = None
    recovery_status: str
    billing_status_snapshot: str | None = None
    subscription_tier_snapshot: str | None = None
    title: str
    summary: str
    first_detected_at: datetime
    last_detected_at: datetime
    resolved_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BillingRecoveryEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recovery_case_id: int
    event_type: str
    summary: str
    created_at: datetime


class BillingRecoveryCaseDetailResponse(BaseModel):
    case: BillingRecoveryCaseRead
    events: list[BillingRecoveryEventRead]


class BillingRecoveryPromptResponse(BaseModel):
    has_open_recovery: bool
    case: BillingRecoveryCaseRead | None = None
    action_label: str | None = None
    action_route: str | None = None
    message: str | None = None


class BillingRecoveryCaseUpdate(BaseModel):
    recovery_status: str | None = None
    notes: str | None = None
    resolved_at: datetime | None = None
    expires_at: datetime | None = None
