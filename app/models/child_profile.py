from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChildProfile(SQLModel, table=True):
    """Child profile owned by a parent account holder."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    display_name: str
    birth_year: int | None = None
    age_band: str = Field(index=True)
    language: str = "en"
    content_lane_key: str | None = Field(default=None, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )


class ChildReadingProfile(SQLModel, table=True):
    """Aggregated taste profile for one child profile."""

    id: int | None = Field(default=None, primary_key=True)
    child_profile_id: int = Field(foreign_key="childprofile.id", unique=True, index=True)
    favorite_characters: str | None = None
    preferred_tones: str | None = None
    preferred_lengths: str | None = None
    preferred_settings: str | None = None
    preferred_styles: str | None = None
    total_books_completed: int = Field(default=0)
    total_books_replayed: int = Field(default=0)
    last_profile_refresh_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
