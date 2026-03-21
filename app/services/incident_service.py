from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from app.models import IncidentRecord, IncidentUpdate, RunbookEntry
from app.models.user import utc_now
from app.schemas.incident_schema import IncidentDetailResponse, IncidentRecordRead, IncidentSummaryResponse, IncidentUpdateRead
from app.services.user_service import get_user_by_id

INCIDENT_SEVERITIES = {"sev_1", "sev_2", "sev_3", "sev_4"}
INCIDENT_STATUSES = {"investigating", "identified", "monitoring", "resolved", "canceled"}
INCIDENT_UPDATE_TYPES = {"status_update", "mitigation_note", "resolution_note", "postmortem_note"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_incident_severity(severity: str) -> str:
    if severity not in INCIDENT_SEVERITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid incident severity")
    return severity


def validate_incident_status(status_value: str) -> str:
    if status_value not in INCIDENT_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid incident status")
    return status_value


def validate_incident_update_type(update_type: str) -> str:
    if update_type not in INCIDENT_UPDATE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid incident update type")
    return update_type


def _validate_assignee(session: Session, *, user_id: int | None) -> None:
    if user_id is None:
        return
    user = get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found")
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user must be an admin")


def get_incident_or_404(session: Session, *, incident_id: int) -> IncidentRecord:
    incident = session.get(IncidentRecord, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


def get_runbook_or_404(session: Session, *, runbook_id: int) -> RunbookEntry:
    runbook = session.get(RunbookEntry, runbook_id)
    if runbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Runbook not found")
    return runbook


def list_incidents(
    session: Session,
    *,
    severity: str | None,
    status_value: str | None,
    affected_area: str | None,
    assigned_to_user_id: int | None,
    limit: int,
) -> list[IncidentRecord]:
    statement = select(IncidentRecord).order_by(IncidentRecord.updated_at.desc()).limit(limit)
    if severity is not None:
        statement = statement.where(IncidentRecord.severity == validate_incident_severity(severity))
    if status_value is not None:
        statement = statement.where(IncidentRecord.status == validate_incident_status(status_value))
    if affected_area is not None and affected_area.strip():
        statement = statement.where(IncidentRecord.affected_area == affected_area.strip())
    if assigned_to_user_id is not None:
        statement = statement.where(IncidentRecord.assigned_to_user_id == assigned_to_user_id)
    return list(session.exec(statement).all())


def create_incident(
    session: Session,
    *,
    title: str,
    summary: str,
    severity: str,
    status_value: str,
    affected_area: str,
    feature_flag_key: str | None,
    assigned_to_user_id: int | None,
    started_at,
    detected_at,
    customer_impact_summary: str | None,
    created_by_user_id: int | None,
) -> IncidentRecord:
    _validate_assignee(session, user_id=assigned_to_user_id)
    normalized_status = validate_incident_status(status_value)
    incident = IncidentRecord(
        title=title.strip(),
        summary=summary.strip(),
        severity=validate_incident_severity(severity),
        status=normalized_status,
        affected_area=affected_area.strip(),
        feature_flag_key=feature_flag_key.strip() if feature_flag_key is not None and feature_flag_key.strip() else None,
        assigned_to_user_id=assigned_to_user_id,
        started_at=started_at or utc_now(),
        detected_at=detected_at,
        customer_impact_summary=customer_impact_summary.strip() if customer_impact_summary is not None and customer_impact_summary.strip() else None,
        created_by_user_id=created_by_user_id,
    )
    if normalized_status == "resolved" and incident.resolved_at is None:
        incident.resolved_at = utc_now()
    return _persist(session, incident)


def update_incident(
    session: Session,
    *,
    incident: IncidentRecord,
    title: str | None = None,
    summary: str | None = None,
    severity: str | None = None,
    status_value: str | None = None,
    affected_area: str | None = None,
    feature_flag_key: str | None = None,
    assigned_to_user_id: int | None = None,
    detected_at=None,
    mitigated_at=None,
    resolved_at=None,
    customer_impact_summary: str | None = None,
    root_cause_summary: str | None = None,
    feature_flag_key_provided: bool = False,
    assigned_to_user_id_provided: bool = False,
    detected_at_provided: bool = False,
    mitigated_at_provided: bool = False,
    resolved_at_provided: bool = False,
    customer_impact_summary_provided: bool = False,
    root_cause_summary_provided: bool = False,
) -> IncidentRecord:
    if title is not None:
        incident.title = title.strip()
    if summary is not None:
        incident.summary = summary.strip()
    if severity is not None:
        incident.severity = validate_incident_severity(severity)
    if status_value is not None:
        incident.status = validate_incident_status(status_value)
        if incident.status == "resolved" and incident.resolved_at is None:
            incident.resolved_at = utc_now()
    if affected_area is not None:
        incident.affected_area = affected_area.strip()
    if feature_flag_key_provided:
        incident.feature_flag_key = feature_flag_key.strip() if feature_flag_key is not None and feature_flag_key.strip() else None
    if assigned_to_user_id_provided:
        _validate_assignee(session, user_id=assigned_to_user_id)
        incident.assigned_to_user_id = assigned_to_user_id
    if detected_at_provided:
        incident.detected_at = detected_at
    if mitigated_at_provided:
        incident.mitigated_at = mitigated_at
    if resolved_at_provided:
        incident.resolved_at = resolved_at
    if customer_impact_summary_provided:
        incident.customer_impact_summary = customer_impact_summary.strip() if customer_impact_summary is not None and customer_impact_summary.strip() else None
    if root_cause_summary_provided:
        incident.root_cause_summary = root_cause_summary.strip() if root_cause_summary is not None and root_cause_summary.strip() else None
    incident.updated_at = utc_now()
    return _persist(session, incident)


def add_incident_update(
    session: Session,
    *,
    incident: IncidentRecord,
    author_user_id: int | None,
    update_type: str,
    body: str,
) -> IncidentUpdate:
    if author_user_id is not None:
        _validate_assignee(session, user_id=author_user_id)
    update = IncidentUpdate(
        incident_id=incident.id,
        author_user_id=author_user_id,
        update_type=validate_incident_update_type(update_type),
        body=body.strip(),
    )
    return _persist(session, update)


def list_incident_updates(session: Session, *, incident_id: int) -> list[IncidentUpdate]:
    return list(
        session.exec(
            select(IncidentUpdate)
            .where(IncidentUpdate.incident_id == incident_id)
            .order_by(IncidentUpdate.created_at.asc(), IncidentUpdate.id.asc())
        ).all()
    )


def get_incident_detail(session: Session, *, incident_id: int) -> IncidentDetailResponse:
    incident = get_incident_or_404(session, incident_id=incident_id)
    updates = list_incident_updates(session, incident_id=incident_id)
    return IncidentDetailResponse(
        incident=IncidentRecordRead.model_validate(incident),
        updates=[IncidentUpdateRead.model_validate(item) for item in updates],
    )


def resolve_incident(session: Session, *, incident: IncidentRecord, resolution_note: str | None = None, author_user_id: int | None = None) -> IncidentRecord:
    incident.status = "resolved"
    if incident.resolved_at is None:
        incident.resolved_at = utc_now()
    incident.updated_at = utc_now()
    incident = _persist(session, incident)
    if resolution_note is not None and resolution_note.strip():
        add_incident_update(
            session,
            incident=incident,
            author_user_id=author_user_id,
            update_type="resolution_note",
            body=resolution_note,
        )
    return incident


def get_incident_summary(session: Session) -> IncidentSummaryResponse:
    open_statuses = ["investigating", "identified", "monitoring"]
    resolved_cutoff = utc_now() - timedelta(days=30)
    open_incidents = session.exec(
        select(func.count()).select_from(IncidentRecord).where(IncidentRecord.status.in_(open_statuses))
    ).one()
    sev_1_open = session.exec(
        select(func.count()).select_from(IncidentRecord).where(
            IncidentRecord.status.in_(open_statuses),
            IncidentRecord.severity == "sev_1",
        )
    ).one()
    sev_2_open = session.exec(
        select(func.count()).select_from(IncidentRecord).where(
            IncidentRecord.status.in_(open_statuses),
            IncidentRecord.severity == "sev_2",
        )
    ).one()
    incidents_resolved_30d = session.exec(
        select(func.count()).select_from(IncidentRecord).where(
            IncidentRecord.status == "resolved",
            IncidentRecord.resolved_at >= resolved_cutoff,
        )
    ).one()
    return IncidentSummaryResponse(
        open_incidents=int(open_incidents or 0),
        sev_1_open=int(sev_1_open or 0),
        sev_2_open=int(sev_2_open or 0),
        incidents_resolved_30d=int(incidents_resolved_30d or 0),
    )


def list_runbooks(
    session: Session,
    *,
    area: str | None,
    is_active: bool | None,
    limit: int,
) -> list[RunbookEntry]:
    statement = select(RunbookEntry).order_by(RunbookEntry.area.asc(), RunbookEntry.title.asc()).limit(limit)
    if area is not None and area.strip():
        statement = statement.where(RunbookEntry.area == area.strip())
    if is_active is not None:
        statement = statement.where(RunbookEntry.is_active == is_active)
    return list(session.exec(statement).all())


def create_runbook(
    session: Session,
    *,
    key: str,
    title: str,
    area: str,
    summary: str,
    steps_markdown: str,
    is_active: bool,
    created_by_user_id: int | None,
) -> RunbookEntry:
    existing = session.exec(select(RunbookEntry).where(RunbookEntry.key == key.strip())).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Runbook key already exists")
    runbook = RunbookEntry(
        key=key.strip(),
        title=title.strip(),
        area=area.strip(),
        summary=summary.strip(),
        steps_markdown=steps_markdown.strip(),
        is_active=is_active,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, runbook)


def update_runbook(
    session: Session,
    *,
    runbook: RunbookEntry,
    key: str | None = None,
    title: str | None = None,
    area: str | None = None,
    summary: str | None = None,
    steps_markdown: str | None = None,
    is_active: bool | None = None,
) -> RunbookEntry:
    if key is not None and key.strip() != runbook.key:
        existing = session.exec(select(RunbookEntry).where(RunbookEntry.key == key.strip())).first()
        if existing is not None and existing.id != runbook.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Runbook key already exists")
        runbook.key = key.strip()
    if title is not None:
        runbook.title = title.strip()
    if area is not None:
        runbook.area = area.strip()
    if summary is not None:
        runbook.summary = summary.strip()
    if steps_markdown is not None:
        runbook.steps_markdown = steps_markdown.strip()
    if is_active is not None:
        runbook.is_active = is_active
    runbook.updated_at = utc_now()
    return _persist(session, runbook)
