from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ChildComfortProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    child_profile_id: int = Field(foreign_key="childprofile.id", unique=True, index=True)
    favorite_characters_csv: str | None = None
    favorite_moods_csv: str | None = None
    favorite_story_types_csv: str | None = None
    avoid_tags_csv: str | None = None
    preferred_language: str | None = None
    prefer_narration: bool = Field(default=False)
    prefer_shorter_stories: bool = Field(default=False)
    extra_calm_mode: bool = Field(default=False)
    bedtime_notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
