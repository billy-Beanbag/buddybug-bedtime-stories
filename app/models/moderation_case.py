from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ModerationCase(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    case_type: str = Field(index=True)
    target_type: str = Field(index=True)
    target_id: int | None = Field(default=None, index=True)
    source_type: str = Field(index=True)
    source_id: int | None = Field(default=None, index=True)
    severity: str = Field(index=True)
    status: str = Field(default="open", index=True)
    summary: str
    notes: str | None = None
    assigned_to_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
    resolved_at: datetime | None = None
