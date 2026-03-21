from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class BillingRecoveryCase(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    source_type: str = Field(index=True)
    external_reference: str | None = Field(default=None, index=True)
    recovery_status: str = Field(default="open", index=True)
    billing_status_snapshot: str | None = None
    subscription_tier_snapshot: str | None = None
    title: str
    summary: str
    first_detected_at: datetime = Field(default_factory=utc_now, nullable=False)
    last_detected_at: datetime = Field(default_factory=utc_now, nullable=False)
    resolved_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
