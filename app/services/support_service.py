from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, SupportTicket, SupportTicketNote, User
from app.services.moderation_service import escalate_support_ticket_if_needed
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.review_service import utc_now
from app.services.user_service import get_user_by_id

SUPPORT_TICKET_CATEGORIES = {
    "general_support",
    "billing_issue",
    "bug_report",
    "content_concern",
    "feature_request",
    "parental_controls_question",
}
SUPPORT_TICKET_STATUSES = {"open", "in_progress", "waiting_for_user", "resolved", "closed"}
SUPPORT_TICKET_PRIORITIES = {"low", "normal", "high", "urgent"}
SUPPORT_TICKET_SOURCES = {"app", "web", "internal"}
SUPPORT_NOTE_TYPES = {"staff_note", "user_reply", "system_note"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _validate_category(category: str) -> str:
    if category not in SUPPORT_TICKET_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported support ticket category")
    return category


def _validate_status(status_value: str) -> str:
    if status_value not in SUPPORT_TICKET_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported support ticket status")
    return status_value


def _validate_priority(priority: str) -> str:
    if priority not in SUPPORT_TICKET_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported support ticket priority")
    return priority


def _validate_source(source: str) -> str:
    if source not in SUPPORT_TICKET_SOURCES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported support ticket source")
    return source


def _validate_note_type(note_type: str) -> str:
    if note_type not in SUPPORT_NOTE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported support note type")
    return note_type


def _validate_book_exists(session: Session, *, related_book_id: int | None) -> Book | None:
    if related_book_id is None:
        return None
    book = session.get(Book, related_book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Related book not found")
    return book


def _validate_assignee(session: Session, *, assigned_to_user_id: int | None) -> User | None:
    if assigned_to_user_id is None:
        return None
    assignee = get_user_by_id(session, assigned_to_user_id)
    if assignee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found")
    if not assignee.is_admin and not assignee.is_editor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user must be editor or admin")
    return assignee


def create_support_ticket(
    session: Session,
    *,
    current_user: User | None,
    category: str,
    subject: str,
    message: str,
    email: str | None,
    child_profile_id: int | None,
    related_book_id: int | None,
    source: str,
) -> SupportTicket:
    if current_user is None and not (email and email.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required for unauthenticated tickets")
    _validate_category(category)
    _validate_source(source)
    if current_user is None and child_profile_id is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for child profile support")
    if current_user is not None:
        validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    _validate_book_exists(session, related_book_id=related_book_id)
    # Placeholder hook: future email delivery or helpdesk forwarding can be attached here.
    ticket = SupportTicket(
        user_id=current_user.id if current_user is not None else None,
        child_profile_id=child_profile_id,
        email=(current_user.email if current_user is not None else email.strip() if email else None),
        category=category,
        subject=subject.strip(),
        message=message.strip(),
        related_book_id=related_book_id,
        status="open",
        priority="normal",
        source=source,
    )
    ticket = _persist(session, ticket)
    escalate_support_ticket_if_needed(session, ticket=ticket)
    return ticket


def list_tickets_for_user(
    session: Session,
    *,
    user_id: int,
    status_value: str | None,
    category: str | None,
    limit: int,
) -> list[SupportTicket]:
    statement = select(SupportTicket).where(SupportTicket.user_id == user_id).order_by(SupportTicket.updated_at.desc()).limit(limit)
    if status_value is not None:
        statement = statement.where(SupportTicket.status == _validate_status(status_value))
    if category is not None:
        statement = statement.where(SupportTicket.category == _validate_category(category))
    return list(session.exec(statement).all())


def list_tickets_for_staff(
    session: Session,
    *,
    status_value: str | None,
    priority: str | None,
    category: str | None,
    assigned_to_user_id: int | None,
    limit: int,
) -> list[SupportTicket]:
    statement = select(SupportTicket).order_by(SupportTicket.updated_at.desc()).limit(limit)
    if status_value is not None:
        statement = statement.where(SupportTicket.status == _validate_status(status_value))
    if priority is not None:
        statement = statement.where(SupportTicket.priority == _validate_priority(priority))
    if category is not None:
        statement = statement.where(SupportTicket.category == _validate_category(category))
    if assigned_to_user_id is not None:
        statement = statement.where(SupportTicket.assigned_to_user_id == assigned_to_user_id)
    return list(session.exec(statement).all())


def get_ticket_or_404(session: Session, *, ticket_id: int) -> SupportTicket:
    ticket = session.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    return ticket


def get_ticket_for_user(session: Session, *, ticket_id: int, user_id: int) -> SupportTicket:
    ticket = get_ticket_or_404(session, ticket_id=ticket_id)
    if ticket.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")
    return ticket


def get_ticket_notes(session: Session, *, ticket_id: int, include_internal: bool) -> list[SupportTicketNote]:
    statement = select(SupportTicketNote).where(SupportTicketNote.ticket_id == ticket_id).order_by(SupportTicketNote.created_at.asc())
    if not include_internal:
        statement = statement.where(SupportTicketNote.is_internal.is_(False))
    return list(session.exec(statement).all())


def get_ticket_detail_for_user(session: Session, *, ticket_id: int, user_id: int) -> tuple[SupportTicket, list[SupportTicketNote]]:
    ticket = get_ticket_for_user(session, ticket_id=ticket_id, user_id=user_id)
    notes = get_ticket_notes(session, ticket_id=ticket.id, include_internal=False)
    return ticket, notes


def get_ticket_detail_for_staff(session: Session, *, ticket_id: int) -> tuple[SupportTicket, list[SupportTicketNote]]:
    ticket = get_ticket_or_404(session, ticket_id=ticket_id)
    notes = get_ticket_notes(session, ticket_id=ticket.id, include_internal=True)
    return ticket, notes


def update_ticket(
    session: Session,
    *,
    ticket: SupportTicket,
    status_value: str | None = None,
    priority: str | None = None,
    assigned_to_user_id: int | None = None,
    subject: str | None = None,
    message: str | None = None,
    resolved_at=None,
) -> SupportTicket:
    if status_value is not None:
        ticket.status = _validate_status(status_value)
        if ticket.status in {"resolved", "closed"} and ticket.resolved_at is None:
            ticket.resolved_at = utc_now()
        elif ticket.status not in {"resolved", "closed"}:
            ticket.resolved_at = resolved_at
    if priority is not None:
        ticket.priority = _validate_priority(priority)
    if assigned_to_user_id is not None:
        _validate_assignee(session, assigned_to_user_id=assigned_to_user_id)
        ticket.assigned_to_user_id = assigned_to_user_id
    if subject is not None:
        ticket.subject = subject.strip()
    if message is not None:
        ticket.message = message.strip()
    if resolved_at is not None:
        ticket.resolved_at = resolved_at
    ticket.updated_at = utc_now()
    return _persist(session, ticket)


def add_ticket_note(
    session: Session,
    *,
    ticket: SupportTicket,
    author_user_id: int | None,
    body: str,
    note_type: str,
    is_internal: bool,
) -> SupportTicketNote:
    note = SupportTicketNote(
        ticket_id=ticket.id,
        author_user_id=author_user_id,
        body=body.strip(),
        note_type=_validate_note_type(note_type),
        is_internal=is_internal,
    )
    return _persist(session, note)


def resolve_ticket(session: Session, *, ticket: SupportTicket) -> SupportTicket:
    ticket.status = "resolved"
    ticket.resolved_at = utc_now()
    ticket.updated_at = utc_now()
    return _persist(session, ticket)


def close_ticket(session: Session, *, ticket: SupportTicket) -> SupportTicket:
    ticket.status = "closed"
    if ticket.resolved_at is None:
        ticket.resolved_at = utc_now()
    ticket.updated_at = utc_now()
    return _persist(session, ticket)
