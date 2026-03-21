from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class PublicStatusComponent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    name: str
    description: str | None = None
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    current_status: str = Field(default="operational", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
