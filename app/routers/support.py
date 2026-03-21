from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.support_schema import (
    SupportTicketCreate,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
    SupportTicketNoteCreate,
    SupportTicketNoteRead,
    SupportTicketRead,
    SupportTicketUpdate,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.support_service import (
    add_ticket_note,
    close_ticket,
    create_support_ticket,
    get_ticket_detail_for_staff,
    get_ticket_detail_for_user,
    get_ticket_or_404,
    list_tickets_for_staff,
    list_tickets_for_user,
    resolve_ticket,
    update_ticket,
)
from app.utils.dependencies import get_current_active_user, get_current_editor_user, get_optional_current_user

router = APIRouter(prefix="/support", tags=["support"])
admin_router = APIRouter(prefix="/admin/support", tags=["admin-support"])


@router.get("/me", response_model=SupportTicketListResponse, summary="List current user support tickets")
def get_my_support_tickets(
    status_value: str | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SupportTicketListResponse:
    items = list_tickets_for_user(
        session,
        user_id=current_user.id,
        status_value=status_value,
        category=category,
        limit=limit,
    )
    return SupportTicketListResponse(items=[SupportTicketRead.model_validate(item) for item in items])


@router.get("/me/{ticket_id}", response_model=SupportTicketDetailResponse, summary="Get one current user support ticket")
def get_my_support_ticket_detail(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SupportTicketDetailResponse:
    ticket, notes = get_ticket_detail_for_user(session, ticket_id=ticket_id, user_id=current_user.id)
    return SupportTicketDetailResponse(
        ticket=SupportTicketRead.model_validate(ticket),
        notes=[SupportTicketNoteRead.model_validate(note) for note in notes],
    )


@router.post("/tickets", response_model=SupportTicketRead, status_code=status.HTTP_201_CREATED, summary="Create a support ticket")
def post_support_ticket(
    payload: SupportTicketCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> SupportTicketRead:
    ticket = create_support_ticket(
        session,
        current_user=current_user,
        category=payload.category,
        subject=payload.subject,
        message=payload.message,
        email=payload.email,
        child_profile_id=payload.child_profile_id,
        related_book_id=payload.related_book_id,
        source=payload.source,
    )
    track_event_safe(
        session,
        event_name="support_ticket_created",
        user=current_user,
        child_profile_id=ticket.child_profile_id,
        book_id=ticket.related_book_id,
        metadata={"category": ticket.category, "source": ticket.source, "ticket_id": ticket.id},
    )
    create_audit_log(
        session,
        action_type="support_ticket_created",
        entity_type="support_ticket",
        entity_id=str(ticket.id),
        summary=f"Created support ticket {ticket.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"category": ticket.category, "source": ticket.source},
    )
    return ticket


@admin_router.get("/tickets", response_model=SupportTicketListResponse, summary="List support tickets for staff triage")
def get_staff_support_tickets(
    status_value: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    category: str | None = Query(default=None),
    assigned_to_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> SupportTicketListResponse:
    items = list_tickets_for_staff(
        session,
        status_value=status_value,
        priority=priority,
        category=category,
        assigned_to_user_id=assigned_to_user_id,
        limit=limit,
    )
    return SupportTicketListResponse(items=[SupportTicketRead.model_validate(item) for item in items])


@admin_router.get("/tickets/{ticket_id}", response_model=SupportTicketDetailResponse, summary="Get one support ticket for staff")
def get_staff_support_ticket_detail(
    ticket_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> SupportTicketDetailResponse:
    ticket, notes = get_ticket_detail_for_staff(session, ticket_id=ticket_id)
    return SupportTicketDetailResponse(
        ticket=SupportTicketRead.model_validate(ticket),
        notes=[SupportTicketNoteRead.model_validate(note) for note in notes],
    )


@admin_router.patch("/tickets/{ticket_id}", response_model=SupportTicketRead, summary="Update a support ticket")
def patch_support_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> SupportTicketRead:
    ticket = get_ticket_or_404(session, ticket_id=ticket_id)
    updated = update_ticket(
        session,
        ticket=ticket,
        status_value=payload.status,
        priority=payload.priority,
        assigned_to_user_id=payload.assigned_to_user_id,
        subject=payload.subject,
        message=payload.message,
        resolved_at=payload.resolved_at,
    )
    create_audit_log(
        session,
        action_type="support_ticket_updated",
        entity_type="support_ticket",
        entity_id=str(updated.id),
        summary=f"Updated support ticket {updated.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return updated


@admin_router.post("/tickets/{ticket_id}/notes", response_model=SupportTicketNoteRead, status_code=status.HTTP_201_CREATED, summary="Add internal support note")
def post_support_ticket_note(
    ticket_id: int,
    payload: SupportTicketNoteCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> SupportTicketNoteRead:
    ticket = get_ticket_or_404(session, ticket_id=ticket_id)
    note = add_ticket_note(
        session,
        ticket=ticket,
        author_user_id=current_user.id,
        body=payload.body,
        note_type=payload.note_type,
        is_internal=payload.is_internal,
    )
    track_event_safe(
        session,
        event_name="support_ticket_note_added_internal",
        user=current_user,
        child_profile_id=ticket.child_profile_id,
        book_id=ticket.related_book_id,
        metadata={"ticket_id": ticket.id, "note_id": note.id},
    )
    create_audit_log(
        session,
        action_type="support_ticket_note_added",
        entity_type="support_ticket_note",
        entity_id=str(note.id),
        summary=f"Added note to support ticket {ticket.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"ticket_id": ticket.id, "note_type": note.note_type, "is_internal": note.is_internal},
    )
    return note


@admin_router.post("/tickets/{ticket_id}/resolve", response_model=SupportTicketRead, summary="Resolve a support ticket")
def resolve_support_ticket(
    ticket_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> SupportTicketRead:
    ticket = get_ticket_or_404(session, ticket_id=ticket_id)
    resolved = resolve_ticket(session, ticket=ticket)
    track_event_safe(
        session,
        event_name="support_ticket_resolved",
        user=current_user,
        child_profile_id=resolved.child_profile_id,
        book_id=resolved.related_book_id,
        metadata={"ticket_id": resolved.id, "category": resolved.category},
    )
    create_audit_log(
        session,
        action_type="support_ticket_resolved",
        entity_type="support_ticket",
        entity_id=str(resolved.id),
        summary=f"Resolved support ticket {resolved.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"category": resolved.category},
    )
    return resolved


@admin_router.post("/tickets/{ticket_id}/close", response_model=SupportTicketRead, summary="Close a support ticket")
def close_support_ticket(
    ticket_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> SupportTicketRead:
    ticket = get_ticket_or_404(session, ticket_id=ticket_id)
    closed = close_ticket(session, ticket=ticket)
    track_event_safe(
        session,
        event_name="support_ticket_closed",
        user=current_user,
        child_profile_id=closed.child_profile_id,
        book_id=closed.related_book_id,
        metadata={"ticket_id": closed.id, "category": closed.category},
    )
    create_audit_log(
        session,
        action_type="support_ticket_closed",
        entity_type="support_ticket",
        entity_id=str(closed.id),
        summary=f"Closed support ticket {closed.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"category": closed.category},
    )
    return closed
