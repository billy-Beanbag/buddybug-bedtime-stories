from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import ApiKey, User
from app.schemas.api_key_schema import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyRead, ApiKeyUpdate
from app.schemas.discovery_schema import DiscoverySearchResponse
from app.schemas.reporting_schema import KPIOverviewResponse
from app.services.api_key_service import create_api_key, deactivate_api_key, get_api_key_or_404, list_api_keys, update_api_key
from app.services.audit_service import create_audit_log
from app.services.discovery_service import list_featured_books
from app.services.reporting_service import get_kpi_overview
from app.utils.dependencies import get_current_admin_user, require_api_scope

admin_router = APIRouter(prefix="/admin/api-keys", tags=["admin-api-keys"])
router = APIRouter(prefix="/integrations", tags=["integrations"])


def _audit_api_key_usage(session: Session, *, request: Request, api_key: ApiKey, scope: str) -> None:
    create_audit_log(
        session,
        action_type="api_key_used",
        entity_type="api_key",
        entity_id=str(api_key.id),
        summary=f"API key '{api_key.name}' used for {scope}",
        actor_user=None,
        request_id=get_request_id_from_request(request),
        metadata={"key_prefix": api_key.key_prefix, "scope": scope, "path": str(request.url.path)},
    )


@admin_router.get("", response_model=list[ApiKeyRead], summary="List API keys")
def get_admin_api_keys(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[ApiKeyRead]:
    return list_api_keys(session)


@admin_router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED, summary="Create API key")
def post_admin_api_key(
    payload: ApiKeyCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> ApiKeyCreateResponse:
    api_key, raw_api_key = create_api_key(
        session,
        name=payload.name,
        scopes=payload.scopes,
        created_by_user_id=current_user.id,
        is_active=payload.is_active,
    )
    create_audit_log(
        session,
        action_type="api_key_created",
        entity_type="api_key",
        entity_id=str(api_key.id),
        summary=f"Created API key '{api_key.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"key_prefix": api_key.key_prefix, "scopes": api_key.scopes},
    )
    return ApiKeyCreateResponse(key=ApiKeyRead.model_validate(api_key), raw_api_key=raw_api_key)


@admin_router.patch("/{key_id}", response_model=ApiKeyRead, summary="Update API key")
def patch_admin_api_key(
    key_id: int,
    payload: ApiKeyUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> ApiKeyRead:
    api_key = get_api_key_or_404(session, key_id)
    updated = update_api_key(
        session,
        api_key=api_key,
        name=payload.name,
        scopes=payload.scopes,
        is_active=payload.is_active,
    )
    create_audit_log(
        session,
        action_type="api_key_updated",
        entity_type="api_key",
        entity_id=str(updated.id),
        summary=f"Updated API key '{updated.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@admin_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate API key")
def delete_admin_api_key(
    key_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Response:
    api_key = get_api_key_or_404(session, key_id)
    deactivate_api_key(session, api_key=api_key)
    create_audit_log(
        session,
        action_type="api_key_deleted",
        entity_type="api_key",
        entity_id=str(api_key.id),
        summary=f"Deactivated API key '{api_key.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"key_prefix": api_key.key_prefix},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/reporting/kpi-overview", response_model=KPIOverviewResponse, summary="Scoped KPI overview integration endpoint")
def get_integration_kpi_overview(
    request: Request,
    days: int | None = Query(default=None, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_scope("reporting.read")),
) -> KPIOverviewResponse:
    _audit_api_key_usage(session, request=request, api_key=api_key, scope="reporting.read")
    return get_kpi_overview(session, days=days, start_date=start_date, end_date=end_date)


@router.get("/discovery/featured", response_model=DiscoverySearchResponse, summary="Scoped featured discovery integration endpoint")
def get_integration_featured_books(
    request: Request,
    age_band: str | None = Query(default=None),
    language: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_scope("books.read")),
) -> DiscoverySearchResponse:
    _audit_api_key_usage(session, request=request, api_key=api_key, scope="books.read")
    return list_featured_books(
        session,
        age_band=age_band,
        language=language,
        content_lane_key=content_lane_key,
        limit=limit,
        current_user=None,
        child_profile_id=None,
    )
