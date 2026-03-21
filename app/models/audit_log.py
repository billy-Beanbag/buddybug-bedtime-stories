from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(SQLModel, table=True):
    """Operational audit trail for important admin and workflow actions."""

    id: int | None = Field(default=None, primary_key=True)
    actor_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    actor_email: str | None = None
    action_type: str = Field(index=True)
    entity_type: str = Field(index=True)
    entity_id: str | None = Field(default=None, index=True)
    summary: str
    metadata_json: str | None = None
    request_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
