from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.moderation_schema import ModerationCaseCreate, ModerationCaseDetailResponse, ModerationCaseRead, ModerationCaseUpdate
from app.services.audit_service import create_audit_log
from app.services.moderation_service import (
    build_case_detail_response,
    create_moderation_case,
    dismiss_moderation_case,
    get_moderation_case_or_404,
    list_moderation_cases,
    resolve_moderation_case,
    update_moderation_case,
)
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/admin/moderation", tags=["moderation"])


@router.get("/cases", response_model=list[ModerationCaseRead], summary="List moderation cases")
def get_moderation_cases(
    status_value: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    case_type: str | None = Query(default=None),
    assigned_to_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[ModerationCaseRead]:
    return list_moderation_cases(
        session,
        status_value=status_value,
        severity=severity,
        case_type=case_type,
        assigned_to_user_id=assigned_to_user_id,
        limit=limit,
    )


@router.get("/cases/{case_id}", response_model=ModerationCaseDetailResponse, summary="Get one moderation case")
def get_moderation_case(
    case_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> ModerationCaseDetailResponse:
    moderation_case = get_moderation_case_or_404(session, case_id=case_id)
    return build_case_detail_response(session, moderation_case=moderation_case)


@router.post("/cases", response_model=ModerationCaseRead, status_code=status.HTTP_201_CREATED, summary="Create moderation case")
def post_moderation_case(
    payload: ModerationCaseCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ModerationCaseRead:
    moderation_case = create_moderation_case(
        session,
        case_type=payload.case_type,
        target_type=payload.target_type,
        target_id=payload.target_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        severity=payload.severity,
        status_value=payload.status,
        summary=payload.summary,
        notes=payload.notes,
        assigned_to_user_id=payload.assigned_to_user_id,
    )
    create_audit_log(
        session,
        action_type="moderation_case_created",
        entity_type="moderation_case",
        entity_id=str(moderation_case.id),
        summary=f"Created moderation case {moderation_case.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return moderation_case


@router.patch("/cases/{case_id}", response_model=ModerationCaseRead, summary="Update moderation case")
def patch_moderation_case(
    case_id: int,
    payload: ModerationCaseUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ModerationCaseRead:
    moderation_case = get_moderation_case_or_404(session, case_id=case_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_moderation_case(
        session,
        moderation_case=moderation_case,
        severity=update_data.get("severity"),
        status_value=update_data.get("status"),
        summary=update_data.get("summary"),
        notes=update_data.get("notes"),
        assigned_to_user_id=update_data.get("assigned_to_user_id"),
        resolved_at=update_data.get("resolved_at"),
        assigned_to_user_id_provided="assigned_to_user_id" in update_data,
        notes_provided="notes" in update_data,
        resolved_at_provided="resolved_at" in update_data,
    )
    create_audit_log(
        session,
        action_type="moderation_case_updated",
        entity_type="moderation_case",
        entity_id=str(updated.id),
        summary=f"Updated moderation case {updated.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@router.post("/cases/{case_id}/resolve", response_model=ModerationCaseRead, summary="Resolve moderation case")
def resolve_case(
    case_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ModerationCaseRead:
    moderation_case = get_moderation_case_or_404(session, case_id=case_id)
    resolved = resolve_moderation_case(session, moderation_case=moderation_case)
    create_audit_log(
        session,
        action_type="moderation_case_resolved",
        entity_type="moderation_case",
        entity_id=str(resolved.id),
        summary=f"Resolved moderation case {resolved.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"status": resolved.status},
    )
    return resolved


@router.post("/cases/{case_id}/dismiss", response_model=ModerationCaseRead, summary="Dismiss moderation case")
def dismiss_case(
    case_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ModerationCaseRead:
    moderation_case = get_moderation_case_or_404(session, case_id=case_id)
    dismissed = dismiss_moderation_case(session, moderation_case=moderation_case)
    create_audit_log(
        session,
        action_type="moderation_case_dismissed",
        entity_type="moderation_case",
        entity_id=str(dismissed.id),
        summary=f"Dismissed moderation case {dismissed.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"status": dismissed.status},
    )
    return dismissed
