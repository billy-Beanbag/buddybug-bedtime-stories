from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.discovery_schema import DiscoverySearchResult


class ReadingPlanCreate(BaseModel):
    child_profile_id: int | None = None
    title: str
    description: str | None = None
    status: str = "active"
    plan_type: str
    preferred_age_band: str | None = None
    preferred_language: str | None = None
    preferred_content_lane_key: str | None = None
    prefer_narration: bool = False
    sessions_per_week: int = Field(default=3, ge=1, le=7)
    target_days_csv: str | None = None
    bedtime_mode_preferred: bool = True


class ReadingPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    child_profile_id: int | None = None
    title: str
    description: str | None = None
    status: str
    plan_type: str
    preferred_age_band: str | None = None
    preferred_language: str | None = None
    preferred_content_lane_key: str | None = None
    prefer_narration: bool
    sessions_per_week: int
    target_days_csv: str | None = None
    bedtime_mode_preferred: bool
    created_at: datetime
    updated_at: datetime


class ReadingPlanUpdate(BaseModel):
    child_profile_id: int | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    plan_type: str | None = None
    preferred_age_band: str | None = None
    preferred_language: str | None = None
    preferred_content_lane_key: str | None = None
    prefer_narration: bool | None = None
    sessions_per_week: int | None = Field(default=None, ge=1, le=7)
    target_days_csv: str | None = None
    bedtime_mode_preferred: bool | None = None


class ReadingPlanSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reading_plan_id: int
    scheduled_date: date
    suggested_book_id: int | None = None
    completed: bool
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ReadingPlanDetailResponse(BaseModel):
    plan: ReadingPlanRead
    upcoming_sessions: list[ReadingPlanSessionRead]


class ReadingPlanSuggestionResponse(BaseModel):
    plan: ReadingPlanRead
    suggested_books: list[DiscoverySearchResult]
