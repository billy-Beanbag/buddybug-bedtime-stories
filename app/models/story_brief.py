from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoryBrief(SQLModel, table=True):
    """Stored narrative brief used to generate and review a story draft."""

    id: int | None = Field(default=None, primary_key=True)
    story_idea_id: int = Field(foreign_key="storyidea.id", index=True, unique=True)
    mode: str
    hook_type: str
    target_age_band: str
    tone: str
    brief_json: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
