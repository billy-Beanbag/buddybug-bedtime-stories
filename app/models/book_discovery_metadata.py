from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookDiscoveryMetadata(SQLModel, table=True):
    """Normalized discovery metadata for lightweight catalog search."""

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", unique=True, index=True)
    searchable_title: str = Field(index=True)
    searchable_summary: str | None = None
    searchable_text: str | None = None
    age_band: str = Field(index=True)
    language: str = Field(index=True)
    content_lane_key: str | None = Field(default=None, index=True)
    tone_tags: str | None = None
    theme_tags: str | None = None
    character_tags: str | None = None
    setting_tags: str | None = None
    style_tags: str | None = None
    bedtime_safe: bool = Field(default=False)
    adventure_level: str | None = None
    is_featured: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
