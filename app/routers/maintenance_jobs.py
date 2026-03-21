from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.maintenance_job_schema import (
    MaintenanceJobCreate,
    MaintenanceJobRead,
    MaintenanceJobRunResponse,
)
from app.services.audit_service import create_audit_log
from app.services.maintenance_job_service import (
    cancel_maintenance_job,
    create_maintenance_job,
    get_maintenance_job_or_404,
    list_maintenance_jobs,
    run_maintenance_job,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/maintenance", tags=["maintenance-jobs"])


def _job_snapshot(job) -> MaintenanceJobRunResponse:
    return MaintenanceJobRunResponse(job=MaintenanceJobRead.model_validate(job))


@router.get("/jobs", response_model=list[MaintenanceJobRead], summary="List maintenance jobs")
def get_jobs(
    status_value: str | None = Query(default=None, alias="status"),
    job_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[MaintenanceJobRead]:
    return list_maintenance_jobs(session, status_value=status_value, job_type=job_type, limit=limit)


@router.get("/jobs/{job_id}", response_model=MaintenanceJobRead, summary="Get maintenance job")
def get_job(
    job_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> MaintenanceJobRead:
    return get_maintenance_job_or_404(session, job_id=job_id)


@router.post("/jobs", response_model=MaintenanceJobRead, status_code=status.HTTP_201_CREATED, summary="Create maintenance job")
def post_job(
    payload: MaintenanceJobCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> MaintenanceJobRead:
    job = create_maintenance_job(
        session,
        key=payload.key,
        title=payload.title,
        description=payload.description,
        job_type=payload.job_type,
        target_scope=payload.target_scope,
        parameters_json=payload.parameters_json,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="maintenance_job_created",
        entity_type="maintenance_job",
        entity_id=str(job.id),
        summary=f"Created maintenance job '{job.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return job


@router.post("/jobs/{job_id}/run", response_model=MaintenanceJobRunResponse, summary="Run maintenance job")
def run_job_now(
    job_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> MaintenanceJobRunResponse:
    job = get_maintenance_job_or_404(session, job_id=job_id)
    request_id = get_request_id_from_request(request)
    create_audit_log(
        session,
        action_type="maintenance_job_run",
        entity_type="maintenance_job",
        entity_id=str(job.id),
        summary=f"Started maintenance job '{job.title}'",
        actor_user=current_user,
        request_id=request_id,
        metadata={"job_type": job.job_type, "target_scope": job.target_scope},
    )
    job = run_maintenance_job(session, job=job)
    if job.status == "succeeded":
        create_audit_log(
            session,
            action_type="maintenance_job_succeeded",
            entity_type="maintenance_job",
            entity_id=str(job.id),
            summary=f"Maintenance job '{job.title}' succeeded",
            actor_user=current_user,
            request_id=request_id,
            metadata={"job_type": job.job_type},
        )
    elif job.status == "failed":
        create_audit_log(
            session,
            action_type="maintenance_job_failed",
            entity_type="maintenance_job",
            entity_id=str(job.id),
            summary=f"Maintenance job '{job.title}' failed",
            actor_user=current_user,
            request_id=request_id,
            metadata={"job_type": job.job_type, "error_message": job.error_message},
        )
    return _job_snapshot(job)


@router.post("/jobs/{job_id}/cancel", response_model=MaintenanceJobRunResponse, summary="Cancel pending maintenance job")
def cancel_job(
    job_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> MaintenanceJobRunResponse:
    job = get_maintenance_job_or_404(session, job_id=job_id)
    job = cancel_maintenance_job(session, job=job)
    create_audit_log(
        session,
        action_type="maintenance_job_canceled",
        entity_type="maintenance_job",
        entity_id=str(job.id),
        summary=f"Canceled maintenance job '{job.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"job_type": job.job_type},
    )
    return _job_snapshot(job)
