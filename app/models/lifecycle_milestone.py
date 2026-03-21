from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class LifecycleMilestone(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    milestone_type: str = Field(index=True)
    occurred_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    title: str
    summary: str | None = None
    source_table: str | None = None
    source_id: str | None = None
    metadata_json: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
