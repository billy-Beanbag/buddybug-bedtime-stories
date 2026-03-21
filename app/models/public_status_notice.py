from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class PublicStatusNotice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    summary: str
    notice_type: str = Field(index=True)
    public_status: str = Field(index=True)
    component_key: str | None = Field(default=None, index=True)
    linked_incident_id: int | None = Field(default=None, foreign_key="incidentrecord.id", index=True)
    starts_at: datetime = Field(default_factory=utc_now, nullable=False)
    ends_at: datetime | None = None
    is_active: bool = Field(default=True)
    is_public: bool = Field(default=True)
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
