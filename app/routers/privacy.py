from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.config import PRIVACY_POLICY_VERSION, TERMS_VERSION
from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import DataRequest, User
from app.schemas.privacy_schema import (
    DataRequestCreate,
    DataRequestRead,
    DataRequestUpdate,
    LegalAcceptanceRead,
    PrivacyDashboardResponse,
    PrivacyPreferenceRead,
    PrivacyPreferenceUpdate,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.privacy_service import (
    create_data_request,
    get_latest_legal_acceptance,
    get_or_create_privacy_preference,
    list_active_data_requests_for_user,
    list_data_requests_for_admin,
    list_data_requests_for_user,
    list_legal_acceptances_for_user,
    process_export_data_request,
    record_legal_acceptance,
    update_data_request,
    update_privacy_preference,
    validate_data_request_access,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/privacy", tags=["privacy"])
admin_router = APIRouter(prefix="/admin/privacy", tags=["admin-privacy"])


def _get_data_request_or_404(session: Session, request_id: int) -> DataRequest:
    data_request = session.get(DataRequest, request_id)
    if data_request is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data request not found")
    return data_request


@router.get("/me", response_model=PrivacyDashboardResponse, summary="Get privacy dashboard")
def get_privacy_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> PrivacyDashboardResponse:
    return PrivacyDashboardResponse(
        latest_terms_acceptance=get_latest_legal_acceptance(session, user_id=current_user.id, document_type="terms_of_service"),
        latest_privacy_acceptance=get_latest_legal_acceptance(session, user_id=current_user.id, document_type="privacy_policy"),
        privacy_preference=get_or_create_privacy_preference(session, user_id=current_user.id),
        active_data_requests=list_active_data_requests_for_user(session, user_id=current_user.id),
    )


@router.get("/me/preferences", response_model=PrivacyPreferenceRead, summary="Get privacy preferences")
def get_my_privacy_preferences(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> PrivacyPreferenceRead:
    return get_or_create_privacy_preference(session, user_id=current_user.id)


@router.patch("/me/preferences", response_model=PrivacyPreferenceRead, summary="Update privacy preferences")
def patch_my_privacy_preferences(
    payload: PrivacyPreferenceUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> PrivacyPreferenceRead:
    preference = update_privacy_preference(session, user_id=current_user.id, payload=payload)
    track_event_safe(
        session,
        event_name="privacy_preferences_updated",
        user=current_user,
        metadata=payload.model_dump(exclude_unset=True),
    )
    create_audit_log(
        session,
        action_type="privacy_preferences_updated",
        entity_type="privacy_preference",
        entity_id=str(preference.id),
        summary=f"Updated privacy preferences for user {current_user.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return preference


@router.post("/me/accept/terms", response_model=LegalAcceptanceRead, summary="Accept current terms of service")
def accept_terms(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> LegalAcceptanceRead:
    acceptance = record_legal_acceptance(
        session,
        user_id=current_user.id,
        document_type="terms_of_service",
        document_version=TERMS_VERSION,
        source="profile_update",
    )
    create_audit_log(
        session,
        action_type="legal_acceptance_recorded",
        entity_type="legal_acceptance",
        entity_id=str(acceptance.id),
        summary=f"Recorded terms acceptance for user {current_user.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"document_type": acceptance.document_type, "document_version": acceptance.document_version},
    )
    return acceptance


@router.post("/me/accept/privacy", response_model=LegalAcceptanceRead, summary="Accept current privacy policy")
def accept_privacy_policy(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> LegalAcceptanceRead:
    acceptance = record_legal_acceptance(
        session,
        user_id=current_user.id,
        document_type="privacy_policy",
        document_version=PRIVACY_POLICY_VERSION,
        source="profile_update",
    )
    create_audit_log(
        session,
        action_type="legal_acceptance_recorded",
        entity_type="legal_acceptance",
        entity_id=str(acceptance.id),
        summary=f"Recorded privacy acceptance for user {current_user.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"document_type": acceptance.document_type, "document_version": acceptance.document_version},
    )
    return acceptance


@router.get("/me/legal", response_model=list[LegalAcceptanceRead], summary="List legal acceptance history")
def get_my_legal_acceptances(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[LegalAcceptanceRead]:
    return list_legal_acceptances_for_user(session, user_id=current_user.id)


@router.get("/me/data-requests", response_model=list[DataRequestRead], summary="List user data requests")
def get_my_data_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[DataRequestRead]:
    return list_data_requests_for_user(session, user_id=current_user.id)


@router.post("/me/data-requests", response_model=DataRequestRead, status_code=status.HTTP_201_CREATED, summary="Create data request")
def post_data_request(
    payload: DataRequestCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> DataRequestRead:
    data_request = create_data_request(
        session,
        user=current_user,
        request_type=payload.request_type,
        child_profile_id=payload.child_profile_id,
        reason=payload.reason,
    )
    track_event_safe(
        session,
        event_name="data_export_requested" if payload.request_type.startswith("export_") else "data_deletion_requested",
        user=current_user,
        child_profile_id=data_request.child_profile_id,
        metadata={"request_id": data_request.id, "request_type": data_request.request_type},
    )
    create_audit_log(
        session,
        action_type="data_request_created",
        entity_type="data_request",
        entity_id=str(data_request.id),
        summary=f"Created data request '{data_request.request_type}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"request_type": data_request.request_type, "child_profile_id": data_request.child_profile_id},
    )
    return data_request


@router.get("/me/data-requests/{request_id}", response_model=DataRequestRead, summary="Get one user data request")
def get_my_data_request(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> DataRequestRead:
    return validate_data_request_access(session, user=current_user, request_id=request_id)


@admin_router.get("/data-requests", response_model=list[DataRequestRead], summary="List privacy data requests")
def admin_list_data_requests(
    status_value: str | None = Query(default=None, alias="status"),
    request_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[DataRequestRead]:
    return list_data_requests_for_admin(session, status_value=status_value, request_type=request_type, limit=limit)


@admin_router.get("/data-requests/{request_id}", response_model=DataRequestRead, summary="Get one privacy data request")
def admin_get_data_request(
    request_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> DataRequestRead:
    return _get_data_request_or_404(session, request_id)


@admin_router.post("/data-requests/{request_id}/process-export", response_model=DataRequestRead, summary="Build export and complete request")
def admin_process_export_data_request(
    request_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> DataRequestRead:
    data_request = _get_data_request_or_404(session, request_id)
    updated = process_export_data_request(session, data_request=data_request)
    create_audit_log(
        session,
        action_type="data_request_completed",
        entity_type="data_request",
        entity_id=str(updated.id),
        summary=f"Completed data request '{updated.request_type}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"request_type": updated.request_type, "output_url": updated.output_url},
    )
    return updated


@admin_router.patch("/data-requests/{request_id}", response_model=DataRequestRead, summary="Update privacy data request")
def admin_patch_data_request(
    request_id: int,
    payload: DataRequestUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> DataRequestRead:
    data_request = _get_data_request_or_404(session, request_id)
    updated = update_data_request(session, data_request=data_request, payload=payload)
    create_audit_log(
        session,
        action_type="data_request_status_updated",
        entity_type="data_request",
        entity_id=str(updated.id),
        summary=f"Updated data request '{updated.request_type}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True, mode="json"),
    )
    return updated
