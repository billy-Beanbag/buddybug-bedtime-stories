from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserStoryFeedback(SQLModel, table=True):
    """Per-user feedback for one published book."""

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", "child_profile_id", name="uq_user_book_child_feedback"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    liked: bool | None = None
    rating: int | None = None
    completed: bool = Field(default=False)
    replayed: bool = Field(default=False)
    preferred_character: str | None = None
    preferred_style: str | None = None
    preferred_tone: str | None = None
    feedback_notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )


class UserStoryProfile(SQLModel, table=True):
    """Simple aggregate taste profile derived from user feedback history."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    favorite_characters: str | None = None
    preferred_tones: str | None = None
    preferred_lengths: str | None = None
    preferred_settings: str | None = None
    preferred_styles: str | None = None
    total_books_rated: int = Field(default=0)
    total_books_completed: int = Field(default=0)
    total_books_replayed: int = Field(default=0)
    last_profile_refresh_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
