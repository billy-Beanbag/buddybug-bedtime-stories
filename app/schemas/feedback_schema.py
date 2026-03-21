from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserStoryFeedbackCreate(BaseModel):
    book_id: int
    child_profile_id: int | None = None
    liked: bool | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    completed: bool = False
    replayed: bool = False
    preferred_character: str | None = None
    preferred_style: str | None = None
    preferred_tone: str | None = None
    feedback_notes: str | None = None


class UserStoryFeedbackUpdate(BaseModel):
    child_profile_id: int | None = None
    liked: bool | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    completed: bool | None = None
    replayed: bool | None = None
    preferred_character: str | None = None
    preferred_style: str | None = None
    preferred_tone: str | None = None
    feedback_notes: str | None = None


class UserStoryFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    child_profile_id: int | None = None
    liked: bool | None = None
    rating: int | None = None
    completed: bool
    replayed: bool
    preferred_character: str | None = None
    preferred_style: str | None = None
    preferred_tone: str | None = None
    feedback_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class UserStoryProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    favorite_characters: str | None = None
    preferred_tones: str | None = None
    preferred_lengths: str | None = None
    preferred_settings: str | None = None
    preferred_styles: str | None = None
    total_books_rated: int
    total_books_completed: int
    total_books_replayed: int
    last_profile_refresh_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class FeedbackSummaryResponse(BaseModel):
    feedback: UserStoryFeedbackRead
    profile: UserStoryProfileRead
