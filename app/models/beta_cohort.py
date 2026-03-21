from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class BetaCohort(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    name: str
    description: str | None = None
    is_active: bool = Field(default=True)
    feature_flag_keys: str | None = None
    notes: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
