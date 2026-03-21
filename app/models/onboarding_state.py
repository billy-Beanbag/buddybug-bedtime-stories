from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OnboardingState(SQLModel, table=True):
    """Tracks lightweight onboarding progress for one family account."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    current_step: str = Field(default="welcome")
    completed: bool = Field(default=False)
    skipped: bool = Field(default=False)
    child_profile_created: bool = Field(default=False)
    preferred_age_band: str | None = None
    preferred_language: str | None = None
    bedtime_mode_reviewed: bool = Field(default=False)
    first_story_opened: bool = Field(default=False)
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
