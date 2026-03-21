from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SupportTicketCreate(BaseModel):
    category: str
    subject: str
    message: str
    email: str | None = None
    child_profile_id: int | None = None
    related_book_id: int | None = None
    source: str = "app"


class SupportTicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    child_profile_id: int | None = None
    email: str | None = None
    category: str
    subject: str
    message: str
    related_book_id: int | None = None
    status: str
    priority: str
    assigned_to_user_id: int | None = None
    source: str
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class SupportTicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to_user_id: int | None = None
    subject: str | None = None
    message: str | None = None
    resolved_at: datetime | None = None


class SupportTicketNoteCreate(BaseModel):
    body: str
    note_type: str = "staff_note"
    is_internal: bool = True


class SupportTicketNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_user_id: int | None = None
    note_type: str
    body: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime


class SupportTicketDetailResponse(BaseModel):
    ticket: SupportTicketRead
    notes: list[SupportTicketNoteRead]


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketRead]
