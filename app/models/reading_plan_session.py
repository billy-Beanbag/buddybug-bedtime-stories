from datetime import date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ReadingPlanSession(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("reading_plan_id", "scheduled_date", name="uq_reading_plan_session_plan_date"),
    )

    id: int | None = Field(default=None, primary_key=True)
    reading_plan_id: int = Field(foreign_key="readingplan.id", index=True)
    scheduled_date: date = Field(index=True)
    suggested_book_id: int | None = Field(default=None, foreign_key="book.id", index=True)
    completed: bool = Field(default=False)
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
