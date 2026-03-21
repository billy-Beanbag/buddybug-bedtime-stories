from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SupportTicketNote(SQLModel, table=True):
    """Ticket note for internal triage and future reply workflows."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="supportticket.id", index=True)
    author_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    note_type: str = Field(default="staff_note", index=True)
    body: str
    is_internal: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
