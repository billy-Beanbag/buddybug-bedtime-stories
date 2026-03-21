from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LegalAcceptance(SQLModel, table=True):
    """Historical record of legal document acceptance by a parent account."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_type: str = Field(index=True)
    document_version: str
    accepted_at: datetime = Field(default_factory=utc_now, nullable=False)
    source: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
