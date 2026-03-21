from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoryStyleTrainingData(SQLModel, table=True):
    """Founder-edited story examples used to sharpen future Buddybug generations."""

    id: int | None = Field(default=None, primary_key=True)
    original_story: str
    edited_story: str
    edit_notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
