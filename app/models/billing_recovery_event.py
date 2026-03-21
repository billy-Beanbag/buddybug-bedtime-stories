from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class BillingRecoveryEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    recovery_case_id: int = Field(foreign_key="billingrecoverycase.id", index=True)
    event_type: str = Field(index=True)
    summary: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
