from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class IncidentRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    summary: str
    severity: str = Field(index=True)
    status: str = Field(default="investigating", index=True)
    affected_area: str = Field(index=True)
    feature_flag_key: str | None = None
    assigned_to_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    started_at: datetime = Field(default_factory=utc_now, nullable=False)
    detected_at: datetime | None = None
    mitigated_at: datetime | None = None
    resolved_at: datetime | None = None
    customer_impact_summary: str | None = None
    root_cause_summary: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
