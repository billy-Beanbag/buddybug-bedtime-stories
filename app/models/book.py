from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Book(SQLModel, table=True):
    """Final assembled book record derived from an approved story draft."""

    id: int | None = Field(default=None, primary_key=True)
    story_draft_id: int = Field(foreign_key="storydraft.id", index=True)
    title: str = Field(index=True)
    cover_image_url: str | None = None
    age_band: str
    content_lane_key: str | None = Field(default="bedtime_3_7", index=True)
    language: str = "en"
    published: bool = False
    publication_status: str = Field(default="ready")
    audio_available: bool = False
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )


class BookPage(SQLModel, table=True):
    """Stable final reading page created from story pages and illustrations."""

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    source_story_page_id: int | None = Field(default=None, foreign_key="storypage.id")
    page_number: int = Field(index=True)
    text_content: str
    image_url: str | None = None
    layout_type: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
