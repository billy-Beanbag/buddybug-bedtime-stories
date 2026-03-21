from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, or_, select

from app.models import IncidentRecord, PublicStatusComponent, PublicStatusNotice
from app.models.user import utc_now
from app.schemas.public_status_schema import PublicStatusPageResponse

PUBLIC_STATUS_VALUES = {
    "operational",
    "degraded_performance",
    "partial_outage",
    "major_outage",
    "maintenance",
}
PUBLIC_NOTICE_TYPES = {"incident", "maintenance", "informational"}
STATUS_PRIORITY = {
    "operational": 0,
    "maintenance": 1,
    "degraded_performance": 2,
    "partial_outage": 3,
    "major_outage": 4,
}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_public_status(value: str) -> str:
    if value not in PUBLIC_STATUS_VALUES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid public status")
    return value


def validate_notice_type(value: str) -> str:
    if value not in PUBLIC_NOTICE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid public notice type")
    return value


def get_public_status_component_or_404(session: Session, *, component_id: int) -> PublicStatusComponent:
    component = session.get(PublicStatusComponent, component_id)
    if component is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public status component not found")
    return component


def get_public_status_notice_or_404(session: Session, *, notice_id: int) -> PublicStatusNotice:
    notice = session.get(PublicStatusNotice, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public status notice not found")
    return notice


def _validate_component_key(session: Session, *, component_key: str | None) -> str | None:
    if component_key is None or not component_key.strip():
        return None
    normalized = component_key.strip().lower()
    component = session.exec(select(PublicStatusComponent).where(PublicStatusComponent.key == normalized)).first()
    if component is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public status component not found")
    return normalized


def _validate_linked_incident(session: Session, *, linked_incident_id: int | None) -> int | None:
    if linked_incident_id is None:
        return None
    incident = session.get(IncidentRecord, linked_incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked incident not found")
    return linked_incident_id


def list_public_components(session: Session, *, public_only: bool = False) -> list[PublicStatusComponent]:
    statement = select(PublicStatusComponent)
    if public_only:
        statement = statement.where(PublicStatusComponent.is_active.is_(True))
    statement = statement.order_by(PublicStatusComponent.sort_order.asc(), PublicStatusComponent.name.asc())
    return list(session.exec(statement).all())


def list_public_status_notices(
    session: Session,
    *,
    notice_type: str | None = None,
    is_active: bool | None = None,
    limit: int = 100,
) -> list[PublicStatusNotice]:
    statement = select(PublicStatusNotice).order_by(PublicStatusNotice.starts_at.desc(), PublicStatusNotice.id.desc()).limit(limit)
    if notice_type is not None:
        statement = statement.where(PublicStatusNotice.notice_type == validate_notice_type(notice_type))
    if is_active is not None:
        statement = statement.where(PublicStatusNotice.is_active.is_(is_active))
    return list(session.exec(statement).all())


def list_active_public_notices(session: Session) -> list[PublicStatusNotice]:
    now = utc_now()
    statement = (
        select(PublicStatusNotice)
        .where(
            PublicStatusNotice.is_public.is_(True),
            PublicStatusNotice.is_active.is_(True),
            PublicStatusNotice.starts_at <= now,
            or_(PublicStatusNotice.ends_at.is_(None), PublicStatusNotice.ends_at >= now),
        )
        .order_by(PublicStatusNotice.starts_at.desc(), PublicStatusNotice.id.desc())
    )
    return list(session.exec(statement).all())


def list_upcoming_maintenance(session: Session) -> list[PublicStatusNotice]:
    now = utc_now()
    statement = (
        select(PublicStatusNotice)
        .where(
            PublicStatusNotice.is_public.is_(True),
            PublicStatusNotice.is_active.is_(True),
            PublicStatusNotice.notice_type == "maintenance",
            PublicStatusNotice.starts_at > now,
        )
        .order_by(PublicStatusNotice.starts_at.asc(), PublicStatusNotice.id.desc())
    )
    return list(session.exec(statement).all())


def compute_overall_public_status(
    *,
    components: list[PublicStatusComponent],
    active_notices: list[PublicStatusNotice],
) -> str:
    statuses = [item.current_status for item in components if item.is_active]
    statuses.extend(item.public_status for item in active_notices if item.is_active and item.is_public)
    if not statuses:
        return "operational"
    return max(statuses, key=lambda item: STATUS_PRIORITY.get(item, 0))


def get_public_status_page(session: Session) -> PublicStatusPageResponse:
    components = list_public_components(session, public_only=True)
    active_notices = list_active_public_notices(session)
    upcoming_maintenance = list_upcoming_maintenance(session)
    return PublicStatusPageResponse(
        overall_status=compute_overall_public_status(components=components, active_notices=active_notices),
        components=components,
        active_notices=active_notices,
        upcoming_maintenance=upcoming_maintenance,
    )


def create_public_status_notice(
    session: Session,
    *,
    title: str,
    summary: str,
    notice_type: str,
    public_status: str,
    component_key: str | None,
    linked_incident_id: int | None,
    starts_at,
    ends_at,
    is_active: bool,
    is_public: bool,
    created_by_user_id: int | None,
) -> PublicStatusNotice:
    normalized_starts_at = starts_at or utc_now()
    normalized_ends_at = ends_at
    if normalized_ends_at is not None and normalized_ends_at < normalized_starts_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ends_at must be after starts_at")
    notice = PublicStatusNotice(
        title=title.strip(),
        summary=summary.strip(),
        notice_type=validate_notice_type(notice_type),
        public_status=validate_public_status(public_status),
        component_key=_validate_component_key(session, component_key=component_key),
        linked_incident_id=_validate_linked_incident(session, linked_incident_id=linked_incident_id),
        starts_at=normalized_starts_at,
        ends_at=normalized_ends_at,
        is_active=is_active,
        is_public=is_public,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, notice)


def update_public_status_notice(
    session: Session,
    *,
    notice: PublicStatusNotice,
    title: str | None = None,
    summary: str | None = None,
    notice_type: str | None = None,
    public_status: str | None = None,
    component_key: str | None = None,
    linked_incident_id: int | None = None,
    starts_at=None,
    ends_at=None,
    is_active: bool | None = None,
    is_public: bool | None = None,
    component_key_provided: bool = False,
    linked_incident_id_provided: bool = False,
    starts_at_provided: bool = False,
    ends_at_provided: bool = False,
) -> PublicStatusNotice:
    if title is not None:
        notice.title = title.strip()
    if summary is not None:
        notice.summary = summary.strip()
    if notice_type is not None:
        notice.notice_type = validate_notice_type(notice_type)
    if public_status is not None:
        notice.public_status = validate_public_status(public_status)
    if component_key_provided:
        notice.component_key = _validate_component_key(session, component_key=component_key)
    if linked_incident_id_provided:
        notice.linked_incident_id = _validate_linked_incident(session, linked_incident_id=linked_incident_id)
    if starts_at_provided:
        notice.starts_at = starts_at
    if ends_at_provided:
        notice.ends_at = ends_at
    if is_active is not None:
        notice.is_active = is_active
    if is_public is not None:
        notice.is_public = is_public
    if notice.ends_at is not None and notice.ends_at < notice.starts_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ends_at must be after starts_at")
    notice.updated_at = utc_now()
    return _persist(session, notice)


def update_public_status_component(
    session: Session,
    *,
    component: PublicStatusComponent,
    current_status: str | None = None,
    is_active: bool | None = None,
    sort_order: int | None = None,
    description: str | None = None,
    name: str | None = None,
    description_provided: bool = False,
    name_provided: bool = False,
) -> PublicStatusComponent:
    if current_status is not None:
        component.current_status = validate_public_status(current_status)
    if is_active is not None:
        component.is_active = is_active
    if sort_order is not None:
        component.sort_order = sort_order
    if description_provided:
        component.description = description.strip() if description is not None and description.strip() else None
    if name_provided:
        if name is None or not name.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Component name cannot be empty")
        component.name = name.strip()
    component.updated_at = utc_now()
    return _persist(session, component)


def delete_public_status_notice(session: Session, *, notice: PublicStatusNotice) -> None:
    session.delete(notice)
    session.commit()
