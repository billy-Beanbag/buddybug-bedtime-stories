from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChildComfortProfileCreate(BaseModel):
    favorite_characters_csv: str | None = None
    favorite_moods_csv: str | None = None
    favorite_story_types_csv: str | None = None
    avoid_tags_csv: str | None = None
    preferred_language: str | None = None
    prefer_narration: bool = False
    prefer_shorter_stories: bool = False
    extra_calm_mode: bool = False
    bedtime_notes: str | None = None


class ChildComfortProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_profile_id: int
    favorite_characters_csv: str | None = None
    favorite_moods_csv: str | None = None
    favorite_story_types_csv: str | None = None
    avoid_tags_csv: str | None = None
    preferred_language: str | None = None
    prefer_narration: bool
    prefer_shorter_stories: bool
    extra_calm_mode: bool
    bedtime_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ChildComfortProfileUpdate(BaseModel):
    favorite_characters_csv: str | None = None
    favorite_moods_csv: str | None = None
    favorite_story_types_csv: str | None = None
    avoid_tags_csv: str | None = None
    preferred_language: str | None = None
    prefer_narration: bool | None = None
    prefer_shorter_stories: bool | None = None
    extra_calm_mode: bool | None = None
    bedtime_notes: str | None = None
