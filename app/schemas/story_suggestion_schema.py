from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class StorySuggestionCreate(SQLModel):
    child_profile_id: int | None = None
    title: str | None = None
    brief: str
    desired_outcome: str | None = None
    inspiration_notes: str | None = None
    avoid_notes: str | None = None
    age_band: str = "3-7"
    language: str = "en"
    allow_reference_use: bool = True


class StorySuggestionRead(StorySuggestionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    promoted_story_idea_id: int | None = None
    status: str
    approved_as_reference: bool
    editorial_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class StorySuggestionAdminRead(StorySuggestionRead):
    user_email: str | None = None
    user_display_name: str | None = None
    child_profile_name: str | None = None
    promoted_story_idea_title: str | None = None


class StorySuggestionAdminUpdate(SQLModel):
    status: str | None = None
    approved_as_reference: bool | None = None
    editorial_notes: str | None = None


class StorySuggestionListResponse(SQLModel):
    items: list[StorySuggestionRead]


class StorySuggestionAdminListResponse(SQLModel):
    items: list[StorySuggestionAdminRead]
