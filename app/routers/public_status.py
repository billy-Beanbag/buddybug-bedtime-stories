from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.public_status_schema import (
    PublicStatusComponentRead,
    PublicStatusComponentUpdate,
    PublicStatusNoticeCreate,
    PublicStatusNoticeRead,
    PublicStatusNoticeUpdate,
    PublicStatusPageResponse,
)
from app.services.audit_service import create_audit_log
from app.services.public_status_service import (
    create_public_status_notice,
    delete_public_status_notice,
    get_public_status_component_or_404,
    get_public_status_notice_or_404,
    get_public_status_page,
    list_active_public_notices,
    list_public_components,
    list_public_status_notices,
    update_public_status_component,
    update_public_status_notice,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(tags=["public-status"])
admin_router = APIRouter(prefix="/admin/status", tags=["admin-public-status"])


@router.get("/status", response_model=PublicStatusPageResponse, summary="Get public status page data")
def get_status_page(session: Session = Depends(get_session)) -> PublicStatusPageResponse:
    return get_public_status_page(session)


@router.get("/status/notices", response_model=list[PublicStatusNoticeRead], summary="List active public notices")
def get_status_notices(session: Session = Depends(get_session)) -> list[PublicStatusNoticeRead]:
    return list_active_public_notices(session)


@admin_router.get("/components", response_model=list[PublicStatusComponentRead], summary="List public status components")
def get_admin_status_components(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[PublicStatusComponentRead]:
    return list_public_components(session, public_only=False)


@admin_router.patch("/components/{component_id}", response_model=PublicStatusComponentRead, summary="Update public status component")
def patch_admin_status_component(
    component_id: int,
    payload: PublicStatusComponentUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> PublicStatusComponentRead:
    component = get_public_status_component_or_404(session, component_id=component_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_public_status_component(
        session,
        component=component,
        current_status=update_data.get("current_status"),
        is_active=update_data.get("is_active"),
        sort_order=update_data.get("sort_order"),
        description=update_data.get("description"),
        name=update_data.get("name"),
        description_provided="description" in update_data,
        name_provided="name" in update_data,
    )
    create_audit_log(
        session,
        action_type="public_status_component_updated",
        entity_type="public_status_component",
        entity_id=str(updated.id),
        summary=f"Updated public status component '{updated.key}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@admin_router.get("/notices", response_model=list[PublicStatusNoticeRead], summary="List public status notices")
def get_admin_status_notices(
    notice_type: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[PublicStatusNoticeRead]:
    return list_public_status_notices(session, notice_type=notice_type, is_active=is_active, limit=limit)


@admin_router.post("/notices", response_model=PublicStatusNoticeRead, status_code=status.HTTP_201_CREATED, summary="Create public status notice")
def post_admin_status_notice(
    payload: PublicStatusNoticeCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> PublicStatusNoticeRead:
    notice = create_public_status_notice(
        session,
        title=payload.title,
        summary=payload.summary,
        notice_type=payload.notice_type,
        public_status=payload.public_status,
        component_key=payload.component_key,
        linked_incident_id=payload.linked_incident_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        is_active=payload.is_active,
        is_public=payload.is_public,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="public_status_notice_created",
        entity_type="public_status_notice",
        entity_id=str(notice.id),
        summary=f"Created public status notice '{notice.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return notice


@admin_router.patch("/notices/{notice_id}", response_model=PublicStatusNoticeRead, summary="Update public status notice")
def patch_admin_status_notice(
    notice_id: int,
    payload: PublicStatusNoticeUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> PublicStatusNoticeRead:
    notice = get_public_status_notice_or_404(session, notice_id=notice_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_public_status_notice(
        session,
        notice=notice,
        title=update_data.get("title"),
        summary=update_data.get("summary"),
        notice_type=update_data.get("notice_type"),
        public_status=update_data.get("public_status"),
        component_key=update_data.get("component_key"),
        linked_incident_id=update_data.get("linked_incident_id"),
        starts_at=update_data.get("starts_at"),
        ends_at=update_data.get("ends_at"),
        is_active=update_data.get("is_active"),
        is_public=update_data.get("is_public"),
        component_key_provided="component_key" in update_data,
        linked_incident_id_provided="linked_incident_id" in update_data,
        starts_at_provided="starts_at" in update_data,
        ends_at_provided="ends_at" in update_data,
    )
    create_audit_log(
        session,
        action_type="public_status_notice_updated",
        entity_type="public_status_notice",
        entity_id=str(updated.id),
        summary=f"Updated public status notice '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@admin_router.delete("/notices/{notice_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete public status notice")
def delete_admin_status_notice(
    notice_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    notice = get_public_status_notice_or_404(session, notice_id=notice_id)
    delete_public_status_notice(session, notice=notice)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
