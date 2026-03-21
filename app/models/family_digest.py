from datetime import date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class FamilyDigest(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "digest_type",
            "period_start",
            "period_end",
            name="uq_family_digest_user_type_period",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    digest_type: str = Field(index=True)
    period_start: date = Field(index=True)
    period_end: date = Field(index=True)
    title: str
    summary_json: str
    generated_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
