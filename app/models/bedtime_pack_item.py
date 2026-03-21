from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class BedtimePackItem(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("bedtime_pack_id", "book_id", name="uq_bedtime_pack_item_pack_book"),
    )

    id: int | None = Field(default=None, primary_key=True)
    bedtime_pack_id: int = Field(foreign_key="bedtimepack.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    position: int
    recommended_narration: bool = Field(default=False)
    completion_status: str = Field(default="pending", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
