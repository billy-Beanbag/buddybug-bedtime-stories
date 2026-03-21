from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ReadAlongParticipant(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "user_id",
            "child_profile_id",
            name="uq_read_along_participant_session_user_child",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="readalongsession.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    role: str = Field(index=True)
    joined_at: datetime = Field(default_factory=utc_now, nullable=False)
    last_seen_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
