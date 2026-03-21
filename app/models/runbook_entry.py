from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class RunbookEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    title: str
    area: str = Field(index=True)
    summary: str
    steps_markdown: str
    is_active: bool = Field(default=True)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
