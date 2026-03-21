from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChildControlOverride(SQLModel, table=True):
    """Child-specific override values; null fields inherit from parent settings."""

    id: int | None = Field(default=None, primary_key=True)
    child_profile_id: int = Field(foreign_key="childprofile.id", unique=True, index=True)
    bedtime_mode_enabled: bool | None = None
    allow_audio_autoplay: bool | None = None
    allow_8_12_content: bool | None = None
    allow_premium_voice_content: bool | None = None
    quiet_mode_enabled: bool | None = None
    max_allowed_age_band: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
