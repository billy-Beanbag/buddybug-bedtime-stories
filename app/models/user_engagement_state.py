from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserEngagementState(SQLModel, table=True):
    """Derived summary of a user's current re-engagement state."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    state_key: str = Field(default="active", index=True)
    last_active_at: datetime | None = None
    last_story_opened_at: datetime | None = None
    last_story_completed_at: datetime | None = None
    last_subscription_active_at: datetime | None = None
    active_child_profiles_count: int = Field(default=0)
    unread_saved_books_count: int = Field(default=0)
    unfinished_books_count: int = Field(default=0)
    preview_only_books_count: int = Field(default=0)
    generated_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
