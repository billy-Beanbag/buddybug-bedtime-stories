from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SeasonalCampaign(SQLModel, table=True):
    """Time-bound themed content campaign for homepage and discovery surfaces."""

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    title: str
    description: str | None = None
    start_at: datetime
    end_at: datetime
    is_active: bool = Field(default=True)
    language: str | None = Field(default=None, index=True)
    age_band: str | None = Field(default=None, index=True)
    content_lane_key: str | None = Field(default=None, index=True)
    homepage_badge_text: str | None = None
    homepage_cta_label: str | None = None
    homepage_cta_route: str | None = None
    banner_style_key: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
