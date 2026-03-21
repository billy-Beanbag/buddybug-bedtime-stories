from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LegalAcceptanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    document_type: str
    document_version: str
    accepted_at: datetime
    source: str
    created_at: datetime


class PrivacyPreferenceCreate(BaseModel):
    marketing_email_opt_in: bool = False
    product_updates_opt_in: bool = True
    analytics_personalization_opt_in: bool = False
    allow_recommendation_personalization: bool = True


class PrivacyPreferenceRead(PrivacyPreferenceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class PrivacyPreferenceUpdate(BaseModel):
    marketing_email_opt_in: bool | None = None
    product_updates_opt_in: bool | None = None
    analytics_personalization_opt_in: bool | None = None
    allow_recommendation_personalization: bool | None = None


class DataRequestCreate(BaseModel):
    request_type: str
    child_profile_id: int | None = None
    reason: str | None = None


class DataRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    request_type: str
    status: str
    reason: str | None = None
    requested_at: datetime
    completed_at: datetime | None = None
    output_url: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DataRequestUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    output_url: str | None = None
    completed_at: datetime | None = None


class PrivacyDashboardResponse(BaseModel):
    latest_terms_acceptance: LegalAcceptanceRead | None
    latest_privacy_acceptance: LegalAcceptanceRead | None
    privacy_preference: PrivacyPreferenceRead | None
    active_data_requests: list[DataRequestRead]
