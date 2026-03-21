from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FeatureFlag(SQLModel, table=True):
    """Stored release flag with lightweight audience targeting."""

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    name: str
    description: str | None = None
    enabled: bool = Field(default=False)
    rollout_percentage: int = Field(default=100, ge=0, le=100)
    environments: str | None = None
    target_subscription_tiers: str | None = None
    target_languages: str | None = None
    target_age_bands: str | None = None
    target_roles: str | None = None
    target_user_ids: str | None = None
    target_countries: str | None = None
    target_beta_cohorts: str | None = None
    is_internal_only: bool = Field(default=False)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
