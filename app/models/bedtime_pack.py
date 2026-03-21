from datetime import date, datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class BedtimePack(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    title: str
    description: str | None = None
    status: str = Field(default="active", index=True)
    pack_type: str = Field(default="nightly", index=True)
    language: str | None = Field(default=None, index=True)
    age_band: str | None = Field(default=None, index=True)
    content_lane_key: str | None = Field(default=None, index=True)
    prefer_narration: bool = Field(default=False)
    generated_reason: str | None = None
    active_date: date | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
