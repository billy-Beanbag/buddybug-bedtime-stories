from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.incident_schema import (
    IncidentDetailResponse,
    IncidentRecordCreate,
    IncidentRecordRead,
    IncidentRecordUpdate,
    IncidentResolveRequest,
    IncidentSummaryResponse,
    IncidentUpdateCreate,
    IncidentUpdateRead,
    RunbookEntryCreate,
    RunbookEntryRead,
    RunbookEntryUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.incident_service import (
    add_incident_update,
    create_incident,
    create_runbook,
    get_incident_detail,
    get_incident_or_404,
    get_incident_summary,
    get_runbook_or_404,
    list_incidents,
    list_runbooks,
    resolve_incident,
    update_incident,
    update_runbook,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["incidents"])


@router.get("/incidents/summary", response_model=IncidentSummaryResponse, summary="Get incident summary")
def get_incidents_summary(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> IncidentSummaryResponse:
    return get_incident_summary(session)


@router.get("/incidents", response_model=list[IncidentRecordRead], summary="List incidents")
def get_incidents(
    severity: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    affected_area: str | None = Query(default=None),
    assigned_to_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[IncidentRecordRead]:
    return list_incidents(
        session,
        severity=severity,
        status_value=status_value,
        affected_area=affected_area,
        assigned_to_user_id=assigned_to_user_id,
        limit=limit,
    )


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse, summary="Get incident detail")
def get_incident(
    incident_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> IncidentDetailResponse:
    return get_incident_detail(session, incident_id=incident_id)


@router.post("/incidents", response_model=IncidentRecordRead, status_code=status.HTTP_201_CREATED, summary="Create incident")
def post_incident(
    payload: IncidentRecordCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> IncidentRecordRead:
    incident = create_incident(
        session,
        title=payload.title,
        summary=payload.summary,
        severity=payload.severity,
        status_value=payload.status,
        affected_area=payload.affected_area,
        feature_flag_key=payload.feature_flag_key,
        assigned_to_user_id=payload.assigned_to_user_id,
        started_at=payload.started_at,
        detected_at=payload.detected_at,
        customer_impact_summary=payload.customer_impact_summary,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="incident_created",
        entity_type="incident_record",
        entity_id=str(incident.id),
        summary=f"Created incident '{incident.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return incident


@router.patch("/incidents/{incident_id}", response_model=IncidentRecordRead, summary="Update incident")
def patch_incident(
    incident_id: int,
    payload: IncidentRecordUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> IncidentRecordRead:
    incident = get_incident_or_404(session, incident_id=incident_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_incident(
        session,
        incident=incident,
        title=update_data.get("title"),
        summary=update_data.get("summary"),
        severity=update_data.get("severity"),
        status_value=update_data.get("status"),
        affected_area=update_data.get("affected_area"),
        feature_flag_key=update_data.get("feature_flag_key"),
        assigned_to_user_id=update_data.get("assigned_to_user_id"),
        detected_at=update_data.get("detected_at"),
        mitigated_at=update_data.get("mitigated_at"),
        resolved_at=update_data.get("resolved_at"),
        customer_impact_summary=update_data.get("customer_impact_summary"),
        root_cause_summary=update_data.get("root_cause_summary"),
        feature_flag_key_provided="feature_flag_key" in update_data,
        assigned_to_user_id_provided="assigned_to_user_id" in update_data,
        detected_at_provided="detected_at" in update_data,
        mitigated_at_provided="mitigated_at" in update_data,
        resolved_at_provided="resolved_at" in update_data,
        customer_impact_summary_provided="customer_impact_summary" in update_data,
        root_cause_summary_provided="root_cause_summary" in update_data,
    )
    create_audit_log(
        session,
        action_type="incident_updated",
        entity_type="incident_record",
        entity_id=str(updated.id),
        summary=f"Updated incident '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@router.post("/incidents/{incident_id}/updates", response_model=IncidentUpdateRead, status_code=status.HTTP_201_CREATED, summary="Add incident update")
def post_incident_update(
    incident_id: int,
    payload: IncidentUpdateCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> IncidentUpdateRead:
    incident = get_incident_or_404(session, incident_id=incident_id)
    update = add_incident_update(
        session,
        incident=incident,
        author_user_id=current_user.id,
        update_type=payload.update_type,
        body=payload.body,
    )
    create_audit_log(
        session,
        action_type="incident_update_added",
        entity_type="incident_record",
        entity_id=str(incident.id),
        summary=f"Added {update.update_type} to incident '{incident.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"incident_update_id": update.id, "update_type": update.update_type},
    )
    return update


@router.post("/incidents/{incident_id}/resolve", response_model=IncidentRecordRead, summary="Resolve incident")
def post_resolve_incident(
    incident_id: int,
    request: Request,
    payload: IncidentResolveRequest | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> IncidentRecordRead:
    incident = get_incident_or_404(session, incident_id=incident_id)
    resolved = resolve_incident(
        session,
        incident=incident,
        resolution_note=payload.body if payload is not None else None,
        author_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="incident_resolved",
        entity_type="incident_record",
        entity_id=str(resolved.id),
        summary=f"Resolved incident '{resolved.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"resolved_at": resolved.resolved_at},
    )
    return resolved


@router.get("/runbooks", response_model=list[RunbookEntryRead], summary="List runbooks")
def get_runbooks(
    area: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[RunbookEntryRead]:
    return list_runbooks(session, area=area, is_active=is_active, limit=limit)


@router.get("/runbooks/{runbook_id}", response_model=RunbookEntryRead, summary="Get runbook")
def get_runbook(
    runbook_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> RunbookEntryRead:
    return get_runbook_or_404(session, runbook_id=runbook_id)


@router.post("/runbooks", response_model=RunbookEntryRead, status_code=status.HTTP_201_CREATED, summary="Create runbook")
def post_runbook(
    payload: RunbookEntryCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> RunbookEntryRead:
    runbook = create_runbook(
        session,
        key=payload.key,
        title=payload.title,
        area=payload.area,
        summary=payload.summary,
        steps_markdown=payload.steps_markdown,
        is_active=payload.is_active,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="runbook_created",
        entity_type="runbook_entry",
        entity_id=str(runbook.id),
        summary=f"Created runbook '{runbook.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return runbook


@router.patch("/runbooks/{runbook_id}", response_model=RunbookEntryRead, summary="Update runbook")
def patch_runbook(
    runbook_id: int,
    payload: RunbookEntryUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> RunbookEntryRead:
    runbook = get_runbook_or_404(session, runbook_id=runbook_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_runbook(
        session,
        runbook=runbook,
        key=update_data.get("key"),
        title=update_data.get("title"),
        area=update_data.get("area"),
        summary=update_data.get("summary"),
        steps_markdown=update_data.get("steps_markdown"),
        is_active=update_data.get("is_active"),
    )
    create_audit_log(
        session,
        action_type="runbook_updated",
        entity_type="runbook_entry",
        entity_id=str(updated.id),
        summary=f"Updated runbook '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@router.delete("/runbooks/{runbook_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate runbook")
def delete_runbook(
    runbook_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Response:
    runbook = get_runbook_or_404(session, runbook_id=runbook_id)
    update_runbook(session, runbook=runbook, is_active=False)
    create_audit_log(
        session,
        action_type="runbook_updated",
        entity_type="runbook_entry",
        entity_id=str(runbook.id),
        summary=f"Deactivated runbook '{runbook.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"is_active": False},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
