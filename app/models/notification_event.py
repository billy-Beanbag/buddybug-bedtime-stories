from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationEvent(SQLModel, table=True):
    """Stored in-app or placeholder delivery notification record."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    notification_type: str = Field(index=True)
    delivery_channel: str = Field(index=True)
    title: str
    body: str
    metadata_json: str | None = None
    is_read: bool = Field(default=False)
    delivered: bool = Field(default=False)
    scheduled_for: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
