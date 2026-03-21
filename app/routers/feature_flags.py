from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import FeatureFlag, User
from app.schemas.feature_flag_schema import (
    FeatureFlagBundleResponse,
    FeatureFlagCreate,
    FeatureFlagEvaluationResponse,
    FeatureFlagRead,
    FeatureFlagUpdate,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.feature_flag_service import (
    build_feature_flag_context,
    evaluate_feature_flag,
    evaluate_feature_flags_for_context,
    get_feature_flag_by_key,
    list_feature_flags,
)
from app.services.review_service import utc_now
from app.utils.dependencies import get_current_admin_user, get_optional_current_user

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])
admin_router = APIRouter(prefix="/admin/feature-flags", tags=["admin-feature-flags"])


def _get_flag_or_404(session: Session, flag_id: int) -> FeatureFlag:
    flag = session.get(FeatureFlag, flag_id)
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")
    return flag


def _persist_flag(session: Session, flag: FeatureFlag) -> FeatureFlag:
    session.add(flag)
    session.commit()
    session.refresh(flag)
    return flag


@router.get("/evaluate/{flag_key}", response_model=FeatureFlagEvaluationResponse, summary="Evaluate one feature flag")
def evaluate_flag(
    flag_key: str,
    request: Request,
    child_profile_id: int | None = Query(default=None),
    language: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> FeatureFlagEvaluationResponse:
    flag = get_feature_flag_by_key(session, flag_key)
    if flag is None:
        return FeatureFlagEvaluationResponse(key=flag_key, enabled=False, reason="flag not found")
    context = build_feature_flag_context(
        session,
        request=request,
        current_user=current_user,
        child_profile_id=child_profile_id,
        language=language,
    )
    return evaluate_feature_flag(flag, context)


@router.get("/bundle", response_model=FeatureFlagBundleResponse, summary="Evaluate frontend feature flag bundle")
def evaluate_flag_bundle(
    request: Request,
    child_profile_id: int | None = Query(default=None),
    language: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> FeatureFlagBundleResponse:
    context = build_feature_flag_context(
        session,
        request=request,
        current_user=current_user,
        child_profile_id=child_profile_id,
        language=language,
    )
    return FeatureFlagBundleResponse(flags=evaluate_feature_flags_for_context(session, context))


@admin_router.get("", response_model=list[FeatureFlagRead], summary="List feature flags")
def admin_list_feature_flags(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[FeatureFlag]:
    return list_feature_flags(session)


@admin_router.get("/{flag_id}", response_model=FeatureFlagRead, summary="Get one feature flag")
def admin_get_feature_flag(
    flag_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> FeatureFlag:
    return _get_flag_or_404(session, flag_id)


@admin_router.post("", response_model=FeatureFlagRead, status_code=status.HTTP_201_CREATED, summary="Create a feature flag")
def admin_create_feature_flag(
    payload: FeatureFlagCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlag:
    if get_feature_flag_by_key(session, payload.key) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feature flag key already exists")
    flag = FeatureFlag.model_validate(payload)
    flag.created_by_user_id = current_user.id
    flag = _persist_flag(session, flag)
    track_event_safe(
        session,
        event_name="feature_flag_admin_updated",
        user=current_user,
        metadata={"action": "created", "flag_id": flag.id, "flag_key": flag.key},
    )
    create_audit_log(
        session,
        action_type="feature_flag_created",
        entity_type="feature_flag",
        entity_id=str(flag.id),
        summary=f"Created feature flag '{flag.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"enabled": flag.enabled, "rollout_percentage": flag.rollout_percentage},
    )
    return flag


@admin_router.patch("/{flag_id}", response_model=FeatureFlagRead, summary="Update a feature flag")
def admin_update_feature_flag(
    flag_id: int,
    payload: FeatureFlagUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlag:
    flag = _get_flag_or_404(session, flag_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "key" in update_data and update_data["key"] != flag.key:
        existing = get_feature_flag_by_key(session, update_data["key"])
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feature flag key already exists")
    if "rollout_percentage" in update_data:
        rollout_percentage = update_data["rollout_percentage"]
        if rollout_percentage is not None and not 0 <= rollout_percentage <= 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rollout_percentage must be between 0 and 100")
    for field_name, value in update_data.items():
        setattr(flag, field_name, value)
    flag.updated_at = utc_now()
    flag = _persist_flag(session, flag)
    track_event_safe(
        session,
        event_name="feature_flag_admin_updated",
        user=current_user,
        metadata={"action": "updated", "flag_id": flag.id, "flag_key": flag.key},
    )
    create_audit_log(
        session,
        action_type="feature_flag_updated",
        entity_type="feature_flag",
        entity_id=str(flag.id),
        summary=f"Updated feature flag '{flag.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return flag


@admin_router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a feature flag")
def admin_delete_feature_flag(
    flag_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Response:
    flag = _get_flag_or_404(session, flag_id)
    flag_key = flag.key
    session.delete(flag)
    session.commit()
    track_event_safe(
        session,
        event_name="feature_flag_admin_updated",
        user=current_user,
        metadata={"action": "deleted", "flag_id": flag_id, "flag_key": flag_key},
    )
    create_audit_log(
        session,
        action_type="feature_flag_deleted",
        entity_type="feature_flag",
        entity_id=str(flag_id),
        summary=f"Deleted feature flag '{flag_key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"flag_key": flag_key},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
