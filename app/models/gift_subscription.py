from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GiftSubscription(SQLModel, table=True):
    """Shareable premium gift code purchased by one parent for another."""

    id: int | None = Field(default=None, primary_key=True)
    purchaser_user_id: int = Field(foreign_key="user.id", index=True)
    recipient_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    code: str = Field(unique=True, index=True)
    duration_days: int
    status: str = Field(default="active", index=True)
    purchased_at: datetime = Field(default_factory=utc_now, nullable=False)
    redeemed_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
