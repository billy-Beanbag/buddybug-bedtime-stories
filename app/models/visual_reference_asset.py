from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class VisualReferenceAsset(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    reference_type: str = Field(index=True)
    target_type: str | None = Field(default=None, index=True)
    target_id: int | None = Field(default=None, index=True)
    image_url: str
    prompt_notes: str | None = None
    language: str | None = None
    is_active: bool = Field(default=True)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
