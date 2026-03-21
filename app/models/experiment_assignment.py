from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExperimentAssignment(SQLModel, table=True):
    """Sticky experiment assignment for a user or anonymous reader."""

    id: int | None = Field(default=None, primary_key=True)
    experiment_key: str = Field(index=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    reader_identifier: str | None = Field(default=None, index=True)
    variant: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
