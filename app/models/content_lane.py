from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContentLane(SQLModel, table=True):
    """Canonical content lane configuration used by generation and quality services."""

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    display_name: str
    age_band: str = Field(index=True)
    description: str | None = None
    tone_rules: str
    writing_rules: str
    illustration_rules: str | None = None
    quality_rules: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
