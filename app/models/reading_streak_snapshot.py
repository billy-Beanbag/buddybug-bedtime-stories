from datetime import date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ReadingStreakSnapshot(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "child_profile_id",
            name="uq_reading_streak_snapshot_user_child",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    current_streak_days: int = Field(default=0)
    longest_streak_days: int = Field(default=0)
    last_read_date: date | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
