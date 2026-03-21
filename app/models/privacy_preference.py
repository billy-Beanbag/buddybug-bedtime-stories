from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyPreference(SQLModel, table=True):
    """Current user privacy and personalization preferences."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    marketing_email_opt_in: bool = Field(default=False)
    product_updates_opt_in: bool = Field(default=True)
    analytics_personalization_opt_in: bool = Field(default=False)
    allow_recommendation_personalization: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
