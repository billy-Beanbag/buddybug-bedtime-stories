from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NarrationSegment(SQLModel, table=True):
    """Page-level narration segment for one narration version."""

    id: int | None = Field(default=None, primary_key=True)
    narration_id: int = Field(foreign_key="booknarration.id", index=True)
    page_number: int = Field(index=True)
    audio_url: str
    duration_seconds: int | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
