from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserLibraryItem(SQLModel, table=True):
    """A saved or archived user-library entry for one book."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    status: str = Field(default="saved", index=True)
    saved_for_offline: bool = Field(default=False)
    last_opened_at: datetime | None = None
    downloaded_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
