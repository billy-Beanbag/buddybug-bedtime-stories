from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoryPage(SQLModel, table=True):
    """Page-level illustration planning record for an approved story draft."""

    id: int | None = Field(default=None, primary_key=True)
    story_draft_id: int = Field(foreign_key="storydraft.id", index=True)
    page_number: int = Field(index=True)
    page_text: str
    scene_summary: str
    location: str
    mood: str
    characters_present: str
    illustration_prompt: str
    image_status: str = Field(default="prompt_ready")
    image_url: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
