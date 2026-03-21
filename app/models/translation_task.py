from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class TranslationTask(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("book_id", "language", name="uq_translation_task_book_language"),)

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    language: str = Field(index=True)
    status: str = Field(default="not_started", index=True)
    assigned_to_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    source_version_label: str | None = None
    notes: str | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
