from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoryIdea(SQLModel, table=True):
    """Structured story idea for later planning, drafting, and review."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    premise: str
    hook_type: str | None = Field(default=None, index=True)
    age_band: str
    content_lane_key: str | None = Field(default="bedtime_3_7", index=True)
    tone: str
    setting: str
    theme: str
    bedtime_feeling: str
    main_characters: str
    supporting_characters: str | None = None
    series_key: str | None = Field(default=None, index=True)
    series_title: str | None = None
    estimated_minutes: int
    status: str = Field(default="idea_pending")
    generation_source: str = Field(default="manual")
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
