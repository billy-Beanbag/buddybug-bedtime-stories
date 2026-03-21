from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class MaintenanceJob(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True)
    title: str
    description: str | None = None
    job_type: str = Field(index=True)
    status: str = Field(default="pending", index=True)
    target_scope: str | None = None
    parameters_json: str | None = None
    result_json: str | None = None
    error_message: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
