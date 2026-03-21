from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NarrationVoice(SQLModel, table=True):
    """Available narration voice option for bedtime story audio."""

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    display_name: str
    description: str | None = None
    language: str = "en"
    gender: str | None = None
    style: str | None = None
    accent: str | None = None
    gender_style: str | None = None
    age_style: str | None = None
    tone_style: str | None = None
    is_premium: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )


class BookAudio(SQLModel, table=True):
    """Narration asset record for one book and voice version."""

    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    voice_id: int = Field(foreign_key="narrationvoice.id", index=True)
    script_source: str
    script_text: str
    audio_url: str
    duration_seconds: int | None = None
    provider: str
    provider_audio_id: str | None = None
    version_number: int = Field(default=1)
    approval_status: str = Field(default="generated")
    is_active: bool = Field(default=False)
    generation_notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
