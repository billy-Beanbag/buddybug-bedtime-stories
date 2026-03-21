from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SupportTicket(SQLModel, table=True):
    """Lightweight support ticket for product operations and feedback intake."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    email: str | None = None
    category: str = Field(index=True)
    subject: str
    message: str
    related_book_id: int | None = Field(default=None, foreign_key="book.id", index=True)
    status: str = Field(default="open", index=True)
    priority: str = Field(default="normal", index=True)
    assigned_to_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    source: str = Field(default="app", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
    resolved_at: datetime | None = None
