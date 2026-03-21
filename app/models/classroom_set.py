from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ClassroomSet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str
    description: str | None = None
    age_band: str | None = Field(default=None, index=True)
    language: str | None = Field(default=None, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
