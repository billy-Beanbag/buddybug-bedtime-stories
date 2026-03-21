from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EditorialAsset(SQLModel, table=True):
    """Project-scoped editorial asset reference."""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="editorialproject.id", index=True)
    asset_type: str = Field(index=True)
    file_url: str
    language: str | None = None
    page_number: int | None = None
    is_active: bool = Field(default=True)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
