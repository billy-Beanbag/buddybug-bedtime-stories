from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EditorialProject(SQLModel, table=True):
    """Editorial workspace for manual or hybrid story publishing."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    description: str | None = None
    age_band: str = Field(index=True)
    content_lane_key: str | None = Field(default=None, index=True)
    language: str = Field(default="en", index=True)
    status: str = Field(default="draft", index=True)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    assigned_editor_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    source_type: str = Field(default="manual", index=True)
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
