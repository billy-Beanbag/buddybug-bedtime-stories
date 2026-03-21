from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AutomationSchedule(SQLModel, table=True):
    """Recurring automation definition that safely creates workflow jobs."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    schedule_type: str = Field(index=True)
    cron_expression: str | None = None
    interval_minutes: int | None = None
    timezone: str | None = None
    job_type: str = Field(index=True)
    payload_json: str
    policy_json: str | None = None
    is_active: bool = Field(default=True)
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    last_job_id: int | None = Field(default=None, foreign_key="workflowjob.id", index=True)
    last_run_status: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
