from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ClassroomSetItem(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("classroom_set_id", "book_id", name="uq_classroom_set_book"),)

    id: int | None = Field(default=None, primary_key=True)
    classroom_set_id: int = Field(foreign_key="classroomset.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    position: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
