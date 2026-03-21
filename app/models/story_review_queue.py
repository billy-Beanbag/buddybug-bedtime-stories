from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoryReviewQueue(SQLModel, table=True):
    """Durable review record for a generated story package before publish."""

    id: int | None = Field(default=None, primary_key=True)
    story_id: int = Field(foreign_key="storydraft.id", index=True, unique=True)
    generated_story: str
    rewritten_story: str
    story_brief: str | None = None
    story_validation: str | None = None
    outline: str
    illustration_plan: str
    story_metadata: str | None = None
    status: str = Field(default="pending_review", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
