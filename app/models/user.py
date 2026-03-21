from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    """Platform user account for future subscriptions and personalization."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    display_name: str | None = None
    country: str | None = None
    language: str = "en"
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    is_editor: bool = Field(default=False)
    is_educator: bool = Field(default=False)
    organization_id: int | None = Field(default=None, foreign_key="organization.id", index=True)
    subscription_tier: str = Field(default="free")
    subscription_status: str = Field(default="none")
    subscription_expires_at: datetime | None = None
    trial_ends_at: datetime | None = None
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
