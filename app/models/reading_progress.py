from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReadingProgress(SQLModel, table=True):
    """Reader/session progress record for one book."""

    __table_args__ = (
        UniqueConstraint("reader_identifier", "book_id", "child_profile_id", name="uq_reader_book_child_progress"),
    )

    id: int | None = Field(default=None, primary_key=True)
    reader_identifier: str = Field(index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    current_page_number: int = Field(default=0)
    completed: bool = Field(default=False)
    last_opened_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
