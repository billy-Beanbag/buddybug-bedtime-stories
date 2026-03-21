from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsEventCreate(BaseModel):
    event_name: str
    user_id: int | None = None
    child_profile_id: int | None = None
    reader_identifier: str | None = None
    book_id: int | None = None
    session_id: str | None = None
    language: str | None = None
    country: str | None = None
    experiment_key: str | None = None
    experiment_variant: str | None = None
    metadata_json: str | None = None


class AnalyticsEventRead(AnalyticsEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    created_at: datetime


class AnalyticsTrackRequest(BaseModel):
    event_name: str
    book_id: int | None = None
    child_profile_id: int | None = None
    session_id: str | None = None
    language: str | None = None
    country: str | None = None
    experiment_key: str | None = None
    experiment_variant: str | None = None
    metadata: dict[str, Any] | None = None


class AnalyticsSummaryResponse(BaseModel):
    total_events: int
    unique_users: int
    unique_readers: int
    top_books: list[dict[str, Any]]
    top_event_counts: dict[str, int]


class ExperimentAssignmentCreate(BaseModel):
    experiment_key: str
    variant: str | None = None
    reader_identifier: str | None = None


class ExperimentAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_key: str
    user_id: int | None = None
    reader_identifier: str | None = None
    variant: str
    created_at: datetime
    updated_at: datetime


class ExperimentConfigRequest(BaseModel):
    experiment_key: str
    variants: list[str] = Field(min_length=2)
    sticky: bool = True


class ExperimentVariantResponse(BaseModel):
    experiment_key: str
    variant: str
    assigned: bool
