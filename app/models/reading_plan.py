from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class ReadingPlan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    child_profile_id: int | None = Field(default=None, foreign_key="childprofile.id", index=True)
    title: str
    description: str | None = None
    status: str = Field(default="active", index=True)
    plan_type: str = Field(index=True)
    preferred_age_band: str | None = Field(default=None, index=True)
    preferred_language: str | None = Field(default=None, index=True)
    preferred_content_lane_key: str | None = Field(default=None, index=True)
    prefer_narration: bool = Field(default=False)
    sessions_per_week: int = Field(default=3)
    target_days_csv: str | None = None
    bedtime_mode_preferred: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
