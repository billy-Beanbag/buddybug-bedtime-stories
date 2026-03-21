from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SeasonalCampaignItem(SQLModel, table=True):
    """Ordered book mapping for a seasonal campaign."""

    __table_args__ = (UniqueConstraint("campaign_id", "book_id", name="uq_seasonal_campaign_book"),)

    id: int | None = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="seasonalcampaign.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    position: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
