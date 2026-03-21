from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class BetaCohortMembership(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("beta_cohort_id", "user_id", name="uq_betacohortmembership_cohort_user"),)

    id: int | None = Field(default=None, primary_key=True)
    beta_cohort_id: int = Field(foreign_key="betacohort.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    source: str = Field(index=True)
    invited_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    is_active: bool = Field(default=True)
    joined_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
