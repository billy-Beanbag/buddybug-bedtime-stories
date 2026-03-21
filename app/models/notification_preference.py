from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationPreference(SQLModel, table=True):
    """Per-user notification preference defaults."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    enable_in_app: bool = Field(default=True)
    enable_email_placeholder: bool = Field(default=False)
    enable_bedtime_reminders: bool = Field(default=True)
    enable_new_story_alerts: bool = Field(default=True)
    enable_weekly_digest: bool = Field(default=False)
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
