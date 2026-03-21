from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookTranslation(SQLModel, table=True):
    """Localized metadata for a published book."""

    __table_args__ = (UniqueConstraint("book_id", "language", name="uq_book_translation_book_language"),)

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    language: str = Field(index=True)
    title: str
    description: str | None = None
    published: bool = False
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )


class BookPageTranslation(SQLModel, table=True):
    """Localized text variant for a final assembled book page."""

    __table_args__ = (
        UniqueConstraint("book_page_id", "language", name="uq_book_page_translation_page_language"),
    )

    id: int | None = Field(default=None, primary_key=True)
    book_page_id: int = Field(foreign_key="bookpage.id", index=True)
    language: str = Field(index=True)
    text_content: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
