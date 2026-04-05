from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClassicSource(SQLModel, table=True):
    """Internal-only imported public-domain classic story source text."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    source_text: str
    source_url: str
    public_domain_verified: bool = Field(default=False, index=True)
    source_author: str | None = None
    source_origin_notes: str | None = None
    import_status: str = Field(default="imported", index=True)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
