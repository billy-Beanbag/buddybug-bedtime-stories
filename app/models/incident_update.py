from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.user import utc_now


class IncidentUpdate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incidentrecord.id", index=True)
    author_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    update_type: str = Field(index=True)
    body: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
