from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ChangelogEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    version_label: str = Field(index=True)
    title: str
    summary: str
    details_markdown: str | None = None
    audience: str = Field(index=True)
    status: str = Field(default="draft", index=True)
    area_tags: str | None = None
    feature_flag_keys: str | None = None
    published_at: datetime | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
