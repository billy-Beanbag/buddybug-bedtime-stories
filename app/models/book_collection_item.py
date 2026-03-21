from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookCollectionItem(SQLModel, table=True):
    """Book membership within a curated collection."""

    __table_args__ = (UniqueConstraint("collection_id", "book_id", name="uq_book_collection_item_collection_book"),)

    id: int | None = Field(default=None, primary_key=True)
    collection_id: int = Field(foreign_key="bookcollection.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    position: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
