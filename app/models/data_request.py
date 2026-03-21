from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DataRequest(SQLModel, table=True):
    """Audit/history record for user export and deletion workflows."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    request_type: str = Field(index=True)
    status: str = Field(default="pending", index=True)
    reason: str | None = None
    requested_at: datetime = Field(default_factory=utc_now, nullable=False)
    completed_at: datetime | None = None
    output_url: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
