from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class FeatureFlagCreate(SQLModel):
    key: str
    name: str
    description: str | None = None
    enabled: bool = False
    rollout_percentage: int = 100
    environments: str | None = None
    target_subscription_tiers: str | None = None
    target_languages: str | None = None
    target_age_bands: str | None = None
    target_roles: str | None = None
    target_user_ids: str | None = None
    target_countries: str | None = None
    target_beta_cohorts: str | None = None
    is_internal_only: bool = False


class FeatureFlagRead(FeatureFlagCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class FeatureFlagUpdate(SQLModel):
    key: str | None = None
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    rollout_percentage: int | None = None
    environments: str | None = None
    target_subscription_tiers: str | None = None
    target_languages: str | None = None
    target_age_bands: str | None = None
    target_roles: str | None = None
    target_user_ids: str | None = None
    target_countries: str | None = None
    target_beta_cohorts: str | None = None
    is_internal_only: bool | None = None


class FeatureFlagEvaluationResponse(SQLModel):
    key: str
    enabled: bool
    reason: str


class FeatureFlagBundleResponse(SQLModel):
    flags: dict[str, bool]
