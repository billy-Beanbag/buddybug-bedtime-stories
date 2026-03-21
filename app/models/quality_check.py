from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QualityCheck(SQLModel, table=True):
    """Deterministic quality/safety result for a generated content target."""

    id: int | None = Field(default=None, primary_key=True)
    target_type: str = Field(index=True)
    target_id: int = Field(index=True)
    check_type: str = Field(index=True)
    status: str = Field(index=True)
    score: float | None = None
    issues_json: str | None = None
    summary: str
    created_by_job_id: int | None = Field(default=None, foreign_key="workflowjob.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
