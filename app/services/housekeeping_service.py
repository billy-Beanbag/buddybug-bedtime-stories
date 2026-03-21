from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    HousekeepingPolicy,
    HousekeepingRun,
    MaintenanceJob,
    NotificationEvent,
    ReengagementSuggestion,
    WorkflowJob,
)
from app.models.user import utc_now

HOUSEKEEPING_ACTION_TYPES = {"report_only", "archive_flag", "soft_cleanup"}
HOUSEKEEPING_RUN_STATUSES = {"pending", "running", "succeeded", "failed", "canceled"}
HOUSEKEEPING_TARGET_TABLES = {
    "notification_events",
    "reengagement_suggestions",
    "maintenance_jobs",
    "workflow_jobs",
}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _serialize_result(value: dict[str, Any]) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    return str(exc)


def validate_target_table(target_table: str) -> str:
    if target_table not in HOUSEKEEPING_TARGET_TABLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid housekeeping target table")
    return target_table


def validate_action_type(action_type: str) -> str:
    if action_type not in HOUSEKEEPING_ACTION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid housekeeping action type")
    return action_type


def validate_run_status(status_value: str) -> str:
    if status_value not in HOUSEKEEPING_RUN_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid housekeeping run status")
    return status_value


def get_housekeeping_policy_or_404(session: Session, *, policy_id: int) -> HousekeepingPolicy:
    policy = session.get(HousekeepingPolicy, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping policy not found")
    return policy


def get_housekeeping_run_or_404(session: Session, *, run_id: int) -> HousekeepingRun:
    run = session.get(HousekeepingRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping run not found")
    return run


def list_housekeeping_policies(session: Session) -> list[HousekeepingPolicy]:
    return list(session.exec(select(HousekeepingPolicy).order_by(HousekeepingPolicy.target_table.asc(), HousekeepingPolicy.name.asc())).all())


def list_housekeeping_runs(
    session: Session,
    *,
    policy_id: int | None,
    status_value: str | None,
    limit: int,
) -> list[HousekeepingRun]:
    statement = select(HousekeepingRun).order_by(HousekeepingRun.created_at.desc()).limit(limit)
    if policy_id is not None:
        statement = statement.where(HousekeepingRun.policy_id == policy_id)
    if status_value is not None:
        statement = statement.where(HousekeepingRun.status == validate_run_status(status_value))
    return list(session.exec(statement).all())


def create_housekeeping_policy(
    session: Session,
    *,
    key: str,
    name: str,
    target_table: str,
    action_type: str,
    retention_days: int,
    enabled: bool,
    dry_run_only: bool,
    notes: str | None,
    created_by_user_id: int | None,
) -> HousekeepingPolicy:
    normalized_key = key.strip()
    existing = session.exec(select(HousekeepingPolicy).where(HousekeepingPolicy.key == normalized_key)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Housekeeping policy key already exists")
    if retention_days < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="retention_days must be at least 1")
    policy = HousekeepingPolicy(
        key=normalized_key,
        name=name.strip(),
        target_table=validate_target_table(target_table),
        action_type=validate_action_type(action_type),
        retention_days=retention_days,
        enabled=enabled,
        dry_run_only=dry_run_only,
        notes=notes.strip() if notes is not None and notes.strip() else None,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, policy)


def update_housekeeping_policy(
    session: Session,
    *,
    policy: HousekeepingPolicy,
    key: str | None = None,
    name: str | None = None,
    target_table: str | None = None,
    action_type: str | None = None,
    retention_days: int | None = None,
    enabled: bool | None = None,
    dry_run_only: bool | None = None,
    notes: str | None = None,
    notes_provided: bool = False,
) -> HousekeepingPolicy:
    if key is not None:
        normalized_key = key.strip()
        if normalized_key != policy.key:
            existing = session.exec(select(HousekeepingPolicy).where(HousekeepingPolicy.key == normalized_key)).first()
            if existing is not None and existing.id != policy.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Housekeeping policy key already exists")
            policy.key = normalized_key
    if name is not None:
        policy.name = name.strip()
    if target_table is not None:
        policy.target_table = validate_target_table(target_table)
    if action_type is not None:
        policy.action_type = validate_action_type(action_type)
    if retention_days is not None:
        if retention_days < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="retention_days must be at least 1")
        policy.retention_days = retention_days
    if enabled is not None:
        policy.enabled = enabled
    if dry_run_only is not None:
        policy.dry_run_only = dry_run_only
    if notes_provided:
        policy.notes = notes.strip() if notes is not None and notes.strip() else None
    policy.updated_at = utc_now()
    return _persist(session, policy)


def create_housekeeping_run(
    session: Session,
    *,
    policy: HousekeepingPolicy,
    dry_run: bool,
    created_by_user_id: int | None,
) -> HousekeepingRun:
    run = HousekeepingRun(
        policy_id=policy.id,
        status="pending",
        dry_run=dry_run,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, run)


def _notification_candidates(session: Session, *, cutoff):
    return list(
        session.exec(
            select(NotificationEvent).where(
                NotificationEvent.delivered.is_(True),
                NotificationEvent.is_read.is_(True),
                NotificationEvent.updated_at <= cutoff,
            )
        ).all()
    )


def handle_notifications_cleanup(session: Session, *, policy: HousekeepingPolicy, dry_run: bool) -> dict[str, Any]:
    cutoff = utc_now() - timedelta(days=policy.retention_days)
    candidates = _notification_candidates(session, cutoff=cutoff)
    effective_action = policy.action_type
    affected_count = 0
    if effective_action == "archive_flag":
        effective_action = "report_only"
    if effective_action == "soft_cleanup" and not dry_run:
        for item in candidates:
            session.delete(item)
        session.commit()
        affected_count = len(candidates)
    return {
        "target_table": policy.target_table,
        "requested_action": policy.action_type,
        "effective_action": effective_action,
        "candidate_count": len(candidates),
        "affected_count": affected_count,
        "cutoff": cutoff.isoformat(),
        "sample_ids": [item.id for item in candidates[:10]],
        "action_downgraded": policy.action_type != effective_action,
    }


def _reengagement_candidates(session: Session, *, cutoff):
    return list(
        session.exec(
            select(ReengagementSuggestion).where(
                ReengagementSuggestion.is_dismissed.is_(True),
                ReengagementSuggestion.updated_at <= cutoff,
            )
        ).all()
    )


def handle_reengagement_cleanup(session: Session, *, policy: HousekeepingPolicy, dry_run: bool) -> dict[str, Any]:
    cutoff = utc_now() - timedelta(days=policy.retention_days)
    candidates = _reengagement_candidates(session, cutoff=cutoff)
    effective_action = policy.action_type
    affected_count = 0
    if effective_action == "archive_flag":
        effective_action = "report_only"
    if effective_action == "soft_cleanup" and not dry_run:
        for item in candidates:
            session.delete(item)
        session.commit()
        affected_count = len(candidates)
    return {
        "target_table": policy.target_table,
        "requested_action": policy.action_type,
        "effective_action": effective_action,
        "candidate_count": len(candidates),
        "affected_count": affected_count,
        "cutoff": cutoff.isoformat(),
        "sample_ids": [item.id for item in candidates[:10]],
        "action_downgraded": policy.action_type != effective_action,
    }


def handle_maintenance_jobs_cleanup(session: Session, *, policy: HousekeepingPolicy, dry_run: bool) -> dict[str, Any]:
    cutoff = utc_now() - timedelta(days=policy.retention_days)
    candidates = list(
        session.exec(
            select(MaintenanceJob).where(
                MaintenanceJob.status.in_(["succeeded", "canceled"]),
                MaintenanceJob.completed_at.is_not(None),
                MaintenanceJob.completed_at <= cutoff,
            )
        ).all()
    )
    return {
        "target_table": policy.target_table,
        "requested_action": policy.action_type,
        "effective_action": "report_only",
        "candidate_count": len(candidates),
        "affected_count": 0,
        "cutoff": cutoff.isoformat(),
        "status_breakdown": {
            "succeeded": sum(1 for item in candidates if item.status == "succeeded"),
            "canceled": sum(1 for item in candidates if item.status == "canceled"),
        },
        "dry_run": dry_run,
        "action_downgraded": policy.action_type != "report_only",
    }


def handle_workflow_jobs_cleanup(session: Session, *, policy: HousekeepingPolicy, dry_run: bool) -> dict[str, Any]:
    cutoff = utc_now() - timedelta(days=policy.retention_days)
    candidates = list(
        session.exec(
            select(WorkflowJob).where(
                WorkflowJob.status == "succeeded",
                WorkflowJob.completed_at.is_not(None),
                WorkflowJob.completed_at <= cutoff,
            )
        ).all()
    )
    job_type_breakdown: dict[str, int] = {}
    for item in candidates:
        job_type_breakdown[item.job_type] = job_type_breakdown.get(item.job_type, 0) + 1
    return {
        "target_table": policy.target_table,
        "requested_action": policy.action_type,
        "effective_action": "report_only",
        "candidate_count": len(candidates),
        "affected_count": 0,
        "cutoff": cutoff.isoformat(),
        "job_type_breakdown": job_type_breakdown,
        "dry_run": dry_run,
        "action_downgraded": policy.action_type != "report_only",
    }


def evaluate_policy_candidates(session: Session, *, policy: HousekeepingPolicy, dry_run: bool) -> dict[str, Any]:
    if policy.target_table == "notification_events":
        return handle_notifications_cleanup(session, policy=policy, dry_run=dry_run)
    if policy.target_table == "reengagement_suggestions":
        return handle_reengagement_cleanup(session, policy=policy, dry_run=dry_run)
    if policy.target_table == "maintenance_jobs":
        return handle_maintenance_jobs_cleanup(session, policy=policy, dry_run=dry_run)
    if policy.target_table == "workflow_jobs":
        return handle_workflow_jobs_cleanup(session, policy=policy, dry_run=dry_run)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported housekeeping target table")


def run_housekeeping_policy(
    session: Session,
    *,
    policy: HousekeepingPolicy,
    dry_run_override: bool | None,
    created_by_user_id: int | None,
) -> HousekeepingRun:
    if not policy.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Housekeeping policy is disabled")
    effective_dry_run = policy.dry_run_only if dry_run_override is None else dry_run_override
    if policy.dry_run_only and effective_dry_run is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This housekeeping policy is dry-run only")
    run = create_housekeeping_run(session, policy=policy, dry_run=effective_dry_run, created_by_user_id=created_by_user_id)
    run.status = "running"
    run.started_at = utc_now()
    run.updated_at = utc_now()
    run = _persist(session, run)
    try:
        result = evaluate_policy_candidates(session, policy=policy, dry_run=effective_dry_run)
        run.status = "succeeded"
        run.candidate_count = int(result.get("candidate_count", 0))
        run.affected_count = int(result.get("affected_count", 0))
        run.result_json = _serialize_result(result)
        run.error_message = None
        run.completed_at = utc_now()
        run.updated_at = utc_now()
        return _persist(session, run)
    except Exception as exc:
        session.rollback()
        failed_run = get_housekeeping_run_or_404(session, run_id=run.id)
        failed_run.status = "failed"
        failed_run.error_message = _error_message(exc)
        failed_run.completed_at = utc_now()
        failed_run.updated_at = utc_now()
        return _persist(session, failed_run)


def handle_recent_runs_summary(session: Session, *, limit: int = 20) -> list[HousekeepingRun]:
    return list(session.exec(select(HousekeepingRun).order_by(HousekeepingRun.created_at.desc()).limit(limit)).all())
