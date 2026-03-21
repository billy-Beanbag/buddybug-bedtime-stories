from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.billing_recovery_schema import (
    BillingRecoveryCaseDetailResponse,
    BillingRecoveryCaseRead,
    BillingRecoveryCaseUpdate,
    BillingRecoveryPromptResponse,
)
from app.services.audit_service import create_audit_log
from app.services.billing_recovery_service import (
    build_recovery_prompt,
    get_billing_recovery_case_or_404,
    list_recovery_cases,
    list_recovery_cases_for_user,
    list_recovery_events,
    resolve_recovery_case,
    update_recovery_case,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/billing-recovery", tags=["billing-recovery"])
admin_router = APIRouter(prefix="/admin/billing-recovery", tags=["admin-billing-recovery"])


@router.get("/me", response_model=BillingRecoveryPromptResponse, summary="Get current billing recovery prompt")
def get_my_billing_recovery_prompt(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> BillingRecoveryPromptResponse:
    return build_recovery_prompt(session, user=current_user)


@router.get("/me/history", response_model=list[BillingRecoveryCaseRead], summary="Get my billing recovery history")
def get_my_billing_recovery_history(
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[BillingRecoveryCaseRead]:
    return list_recovery_cases_for_user(session, user_id=current_user.id, limit=limit)


@admin_router.get("/cases", response_model=list[BillingRecoveryCaseRead], summary="List billing recovery cases")
def get_admin_billing_recovery_cases(
    recovery_status: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[BillingRecoveryCaseRead]:
    return list_recovery_cases(session, recovery_status=recovery_status, user_id=user_id, limit=limit)


@admin_router.get("/cases/{case_id}", response_model=BillingRecoveryCaseDetailResponse, summary="Get billing recovery case detail")
def get_admin_billing_recovery_case_detail(
    case_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> BillingRecoveryCaseDetailResponse:
    recovery_case = get_billing_recovery_case_or_404(session, case_id=case_id)
    return BillingRecoveryCaseDetailResponse(
        case=recovery_case,
        events=list_recovery_events(session, recovery_case_id=recovery_case.id),
    )


@admin_router.patch("/cases/{case_id}", response_model=BillingRecoveryCaseRead, summary="Update billing recovery case")
def patch_admin_billing_recovery_case(
    case_id: int,
    payload: BillingRecoveryCaseUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> BillingRecoveryCaseRead:
    recovery_case = get_billing_recovery_case_or_404(session, case_id=case_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated_case = update_recovery_case(
        session,
        recovery_case=recovery_case,
        recovery_status=update_data.get("recovery_status"),
        notes=update_data.get("notes"),
        resolved_at=update_data.get("resolved_at"),
        expires_at=update_data.get("expires_at"),
        notes_provided="notes" in update_data,
        resolved_at_provided="resolved_at" in update_data,
        expires_at_provided="expires_at" in update_data,
    )
    create_audit_log(
        session,
        action_type="billing_recovery_case_updated",
        entity_type="billing_recovery_case",
        entity_id=str(updated_case.id),
        summary=f"Updated billing recovery case {updated_case.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated_case


@admin_router.post("/cases/{case_id}/resolve", response_model=BillingRecoveryCaseRead, summary="Resolve billing recovery case")
def post_admin_resolve_billing_recovery_case(
    case_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> BillingRecoveryCaseRead:
    recovery_case = get_billing_recovery_case_or_404(session, case_id=case_id)
    return resolve_recovery_case(
        session,
        recovery_case=recovery_case,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        resolution_summary="Billing recovery case resolved by an admin.",
    )
