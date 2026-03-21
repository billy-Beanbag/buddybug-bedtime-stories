from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookCollection(SQLModel, table=True):
    """Curated collection for public or internal discovery surfaces."""

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    title: str
    description: str | None = None
    language: str | None = Field(default=None, index=True)
    age_band: str | None = Field(default=None, index=True)
    content_lane_key: str | None = Field(default=None, index=True)
    is_public: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
