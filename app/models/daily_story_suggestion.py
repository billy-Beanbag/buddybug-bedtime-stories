from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DailyStorySuggestion(SQLModel, table=True):
    """Selected daily story suggestion for one user and optional child context."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    suggestion_date: date = Field(index=True)
    reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
