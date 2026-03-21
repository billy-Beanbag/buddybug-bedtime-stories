from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.housekeeping_schema import (
    HousekeepingPolicyCreate,
    HousekeepingPolicyRead,
    HousekeepingPolicyUpdate,
    HousekeepingRunRead,
    HousekeepingRunResponse,
    HousekeepingSummaryResponse,
)
from app.services.audit_service import create_audit_log
from app.services.housekeeping_service import (
    get_housekeeping_policy_or_404,
    get_housekeeping_run_or_404,
    handle_recent_runs_summary,
    list_housekeeping_policies,
    list_housekeeping_runs,
    create_housekeeping_policy,
    run_housekeeping_policy,
    update_housekeeping_policy,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/housekeeping", tags=["housekeeping"])


def _run_snapshot(run) -> HousekeepingRunResponse:
    return HousekeepingRunResponse(run=HousekeepingRunRead.model_validate(run))


@router.get("/policies", response_model=list[HousekeepingPolicyRead], summary="List housekeeping policies")
def get_policies(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[HousekeepingPolicyRead]:
    return list_housekeeping_policies(session)


@router.get("/policies/{policy_id}", response_model=HousekeepingPolicyRead, summary="Get housekeeping policy")
def get_policy(
    policy_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> HousekeepingPolicyRead:
    return get_housekeeping_policy_or_404(session, policy_id=policy_id)


@router.post("/policies", response_model=HousekeepingPolicyRead, status_code=status.HTTP_201_CREATED, summary="Create housekeeping policy")
def post_policy(
    payload: HousekeepingPolicyCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> HousekeepingPolicyRead:
    policy = create_housekeeping_policy(
        session,
        key=payload.key,
        name=payload.name,
        target_table=payload.target_table,
        action_type=payload.action_type,
        retention_days=payload.retention_days,
        enabled=payload.enabled,
        dry_run_only=payload.dry_run_only,
        notes=payload.notes,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="housekeeping_policy_created",
        entity_type="housekeeping_policy",
        entity_id=str(policy.id),
        summary=f"Created housekeeping policy '{policy.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return policy


@router.patch("/policies/{policy_id}", response_model=HousekeepingPolicyRead, summary="Update housekeeping policy")
def patch_policy(
    policy_id: int,
    payload: HousekeepingPolicyUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> HousekeepingPolicyRead:
    policy = get_housekeeping_policy_or_404(session, policy_id=policy_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_housekeeping_policy(
        session,
        policy=policy,
        key=update_data.get("key"),
        name=update_data.get("name"),
        target_table=update_data.get("target_table"),
        action_type=update_data.get("action_type"),
        retention_days=update_data.get("retention_days"),
        enabled=update_data.get("enabled"),
        dry_run_only=update_data.get("dry_run_only"),
        notes=update_data.get("notes"),
        notes_provided="notes" in update_data,
    )
    create_audit_log(
        session,
        action_type="housekeeping_policy_updated",
        entity_type="housekeeping_policy",
        entity_id=str(updated.id),
        summary=f"Updated housekeeping policy '{updated.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@router.get("/runs", response_model=list[HousekeepingRunRead], summary="List housekeeping runs")
def get_runs(
    policy_id: int | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[HousekeepingRunRead]:
    return list_housekeeping_runs(session, policy_id=policy_id, status_value=status_value, limit=limit)


@router.get("/runs/{run_id}", response_model=HousekeepingRunRead, summary="Get housekeeping run")
def get_run(
    run_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> HousekeepingRunRead:
    return get_housekeeping_run_or_404(session, run_id=run_id)


@router.post("/policies/{policy_id}/run", response_model=HousekeepingRunResponse, summary="Run housekeeping policy")
def run_policy(
    policy_id: int,
    request: Request,
    dry_run: bool | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> HousekeepingRunResponse:
    policy = get_housekeeping_policy_or_404(session, policy_id=policy_id)
    request_id = get_request_id_from_request(request)
    create_audit_log(
        session,
        action_type="housekeeping_run_started",
        entity_type="housekeeping_policy",
        entity_id=str(policy.id),
        summary=f"Started housekeeping run for policy '{policy.name}'",
        actor_user=current_user,
        request_id=request_id,
        metadata={"dry_run": dry_run, "target_table": policy.target_table},
    )
    run = run_housekeeping_policy(session, policy=policy, dry_run_override=dry_run, created_by_user_id=current_user.id)
    if run.status == "succeeded":
        create_audit_log(
            session,
            action_type="housekeeping_run_succeeded",
            entity_type="housekeeping_run",
            entity_id=str(run.id),
            summary=f"Housekeeping run {run.id} succeeded",
            actor_user=current_user,
            request_id=request_id,
            metadata={"policy_id": policy.id, "candidate_count": run.candidate_count, "affected_count": run.affected_count},
        )
    elif run.status == "failed":
        create_audit_log(
            session,
            action_type="housekeeping_run_failed",
            entity_type="housekeeping_run",
            entity_id=str(run.id),
            summary=f"Housekeeping run {run.id} failed",
            actor_user=current_user,
            request_id=request_id,
            metadata={"policy_id": policy.id, "error_message": run.error_message},
        )
    return _run_snapshot(run)


@router.get("/summary", response_model=HousekeepingSummaryResponse, summary="Get housekeeping summary")
def get_summary(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> HousekeepingSummaryResponse:
    return HousekeepingSummaryResponse(
        policies=[HousekeepingPolicyRead.model_validate(item) for item in list_housekeeping_policies(session)],
        recent_runs=[HousekeepingRunRead.model_validate(item) for item in handle_recent_runs_summary(session, limit=20)],
    )
