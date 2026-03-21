from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class ChildProfileCreate(SQLModel):
    display_name: str
    birth_year: int | None = None
    age_band: str
    language: str = "en"
    content_lane_key: str | None = None
    is_active: bool = True


class ChildProfileRead(ChildProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class ChildProfileUpdate(SQLModel):
    display_name: str | None = None
    birth_year: int | None = None
    age_band: str | None = None
    language: str | None = None
    content_lane_key: str | None = None
    is_active: bool | None = None


class ChildReadingProfileRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_profile_id: int
    favorite_characters: str | None = None
    preferred_tones: str | None = None
    preferred_lengths: str | None = None
    preferred_settings: str | None = None
    preferred_styles: str | None = None
    total_books_completed: int
    total_books_replayed: int
    last_profile_refresh_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChildProfileSelectionResponse(SQLModel):
    child_profile: ChildProfileRead
    reading_profile: ChildReadingProfileRead | None = None
