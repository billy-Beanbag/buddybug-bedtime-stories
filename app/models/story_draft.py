from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoryDraft(SQLModel, table=True):
    """Reviewable full story draft generated from a structured story idea."""

    id: int | None = Field(default=None, primary_key=True)
    story_idea_id: int | None = Field(default=None, foreign_key="storyidea.id", index=True)
    project_id: int | None = Field(default=None, foreign_key="editorialproject.id", index=True)
    title: str = Field(index=True)
    age_band: str = Field(default="3-7", index=True)
    language: str = "en"
    content_lane_key: str | None = Field(default="bedtime_3_7", index=True)
    full_text: str
    summary: str
    read_time_minutes: int
    review_status: str = Field(default="draft_pending_review")
    review_notes: str | None = None
    approved_text: str | None = None
    generation_source: str = Field(default="manual")
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
