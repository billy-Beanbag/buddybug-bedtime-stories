from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnalyticsEvent(SQLModel, table=True):
    """First-party product analytics event stored for lightweight reporting."""

    id: int | None = Field(default=None, primary_key=True)
    event_name: str = Field(index=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    reader_identifier: str | None = Field(default=None, index=True)
    book_id: int | None = Field(default=None, foreign_key="book.id", index=True)
    session_id: str | None = Field(default=None, index=True)
    language: str | None = Field(default=None, index=True)
    country: str | None = Field(default=None, index=True)
    experiment_key: str | None = Field(default=None, index=True)
    experiment_variant: str | None = None
    metadata_json: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
