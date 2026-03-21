from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class PromoAccessCode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    name: str
    code: str = Field(unique=True, index=True)
    partner_name: str | None = None
    access_type: str = Field(index=True)
    subscription_tier_granted: str | None = None
    duration_days: int | None = None
    max_redemptions: int | None = None
    redemption_count: int = Field(default=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
