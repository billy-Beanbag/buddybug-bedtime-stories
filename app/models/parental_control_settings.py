from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ParentalControlSettings(SQLModel, table=True):
    """Account-level parental settings for safer family reading defaults."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    bedtime_mode_default: bool = Field(default=True)
    allow_audio_autoplay: bool = Field(default=False)
    allow_8_12_content: bool = Field(default=False)
    allow_premium_voice_content: bool = Field(default=True)
    hide_adventure_content_at_bedtime: bool = Field(default=True)
    max_allowed_age_band: str = Field(default="3-7")
    quiet_mode_default: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
