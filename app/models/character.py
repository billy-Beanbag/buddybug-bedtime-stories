from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Character(SQLModel, table=True):
    """Canonical recurring character used across stories and illustrations."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    role: str
    species: str
    short_description: str
    visual_description: str
    personality_traits: str
    style_rules: str
    color_palette: str | None = None
    accessories: str | None = None
    age_group: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
