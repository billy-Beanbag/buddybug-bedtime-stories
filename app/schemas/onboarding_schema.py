from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OnboardingStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    current_step: str
    completed: bool
    skipped: bool
    child_profile_created: bool
    preferred_age_band: str | None
    preferred_language: str | None
    bedtime_mode_reviewed: bool
    first_story_opened: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OnboardingStateUpdate(BaseModel):
    current_step: str | None = None
    completed: bool | None = None
    skipped: bool | None = None
    child_profile_created: bool | None = None
    preferred_age_band: str | None = None
    preferred_language: str | None = None
    bedtime_mode_reviewed: bool | None = None
    first_story_opened: bool | None = None
    completed_at: datetime | None = None


class OnboardingAdvanceRequest(BaseModel):
    next_step: str | None = None
    preferred_age_band: str | None = None
    preferred_language: str | None = None
    child_profile_created: bool | None = None
    bedtime_mode_reviewed: bool | None = None
    first_story_opened: bool | None = None


class OnboardingStartResponse(BaseModel):
    state: OnboardingStateRead
    recommended_next_route: str
