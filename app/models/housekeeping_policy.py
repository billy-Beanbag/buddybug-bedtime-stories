from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class HousekeepingPolicy(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    name: str
    target_table: str = Field(index=True)
    action_type: str = Field(index=True)
    retention_days: int
    enabled: bool = Field(default=True)
    dry_run_only: bool = Field(default=True)
    notes: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
