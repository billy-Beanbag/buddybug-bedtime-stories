from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ReadAlongSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    join_code: str = Field(unique=True, index=True)
    status: str = Field(default="active", index=True)
    current_page_number: int = Field(default=0)
    playback_state: str = Field(default="paused")
    language: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
    expires_at: datetime | None = None
    ended_at: datetime | None = None
