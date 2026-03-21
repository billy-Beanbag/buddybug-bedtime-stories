from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReengagementSuggestion(SQLModel, table=True):
    """In-app win-back or return-to-reading suggestion."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    suggestion_type: str = Field(index=True)
    title: str
    body: str
    related_book_id: int | None = Field(default=None, foreign_key="book.id", index=True)
    state_key: str | None = Field(default=None, index=True)
    is_dismissed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
