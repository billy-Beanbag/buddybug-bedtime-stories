from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class AccountHealthSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    health_score: int = Field(default=0)
    health_band: str = Field(default="watch", index=True)
    active_children_count: int = Field(default=0)
    stories_opened_30d: int = Field(default=0)
    stories_completed_30d: int = Field(default=0)
    saved_books_count: int = Field(default=0)
    support_tickets_open_count: int = Field(default=0)
    premium_status: str | None = Field(default=None, index=True)
    dormant_days: int | None = None
    snapshot_reasoning: str | None = None
    generated_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
