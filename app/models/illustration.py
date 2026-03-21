from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Illustration(SQLModel, table=True):
    """Generated or uploaded illustration asset tied to a story page."""

    id: int | None = Field(default=None, primary_key=True)
    story_page_id: int = Field(foreign_key="storypage.id", index=True)
    prompt_used: str
    image_url: str
    version_number: int = Field(default=1)
    approval_status: str = Field(default="generated")
    provider: str = Field(default="mock")
    provider_image_id: str | None = None
    generation_notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
