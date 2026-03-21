from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowJob(SQLModel, table=True):
    """Database-backed workflow job for safe asynchronous content automation."""

    id: int | None = Field(default=None, primary_key=True)
    job_type: str = Field(index=True)
    status: str = Field(default="queued", index=True)
    priority: int = Field(default=5)
    payload_json: str
    result_json: str | None = None
    error_message: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    scheduled_for: datetime | None = None
    attempt_count: int = Field(default=0)
    max_attempts: int = Field(default=1)
    parent_job_id: int | None = Field(default=None, foreign_key="workflowjob.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
