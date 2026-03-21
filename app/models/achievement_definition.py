from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class AchievementDefinition(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    title: str
    description: str
    icon_key: str | None = None
    target_scope: str = Field(index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
