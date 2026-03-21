from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from croniter import croniter
from fastapi import BackgroundTasks, HTTPException, status
from sqlmodel import Session, select

from app.models import AutomationSchedule, User
from app.schemas.automation_schema import (
    AutomationPolicyConfig,
    AutomationScheduleCreate,
    AutomationScheduleRead,
    AutomationScheduleRunResponse,
    AutomationScheduleUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.review_service import utc_now
from app.services.workflow_service import WORKFLOW_JOB_TYPES, create_job, run_job_by_id

AUTOMATION_SCHEDULE_TYPES = {"interval", "cron"}
AUTOMATION_LAST_RUN_STATUSES = {"succeeded", "failed", "skipped", "canceled"}
DEFAULT_AUTOMATION_TIMEZONE = "UTC"


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_json(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _deserialize_json(value: str) -> dict[str, Any]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON payload: {exc.msg}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Automation payloads must be JSON objects")
    return data


def parse_policy(value: str | AutomationPolicyConfig | None) -> AutomationPolicyConfig:
    if value is None:
        return AutomationPolicyConfig()
    if isinstance(value, AutomationPolicyConfig):
        return value
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid policy_json: {exc.msg}")
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="policy_json must decode to an object")
    return AutomationPolicyConfig.model_validate(parsed)


def _serialize_policy(policy: AutomationPolicyConfig | None) -> str | None:
    if policy is None:
        return None
    return _serialize_json(policy.model_dump(mode="json"))


def _validate_schedule_type(schedule_type: str) -> str:
    if schedule_type not in AUTOMATION_SCHEDULE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid automation schedule type")
    return schedule_type


def _validate_last_run_status(last_run_status: str | None) -> str | None:
    if last_run_status is None:
        return None
    if last_run_status not in AUTOMATION_LAST_RUN_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid automation last_run_status")
    return last_run_status


def _validate_job_type(job_type: str) -> str:
    if job_type not in WORKFLOW_JOB_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid automation workflow job_type")
    return job_type


def _get_timezone(timezone_name: str | None) -> ZoneInfo:
    candidate = timezone_name or DEFAULT_AUTOMATION_TIMEZONE
    try:
        return ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid automation timezone")


def validate_schedule_type_fields(
    *,
    schedule_type: str,
    cron_expression: str | None,
    interval_minutes: int | None,
    timezone_name: str | None,
) -> None:
    _validate_schedule_type(schedule_type)
    _get_timezone(timezone_name)
    if schedule_type == "interval":
        if interval_minutes is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="interval_minutes is required for interval schedules")
        if cron_expression is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cron_expression is not valid for interval schedules")
        return
    if cron_expression is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cron_expression is required for cron schedules")
    if interval_minutes is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="interval_minutes is not valid for cron schedules")
    try:
        croniter(cron_expression, datetime.now(_get_timezone(timezone_name)))
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cron_expression")


def compute_next_run_for_interval(*, interval_minutes: int, last_run_at: datetime | None, reference_time: datetime | None = None) -> datetime:
    now = reference_time or utc_now()
    normalized_last_run_at = _normalize_datetime(last_run_at)
    if last_run_at is None:
        return now
    return normalized_last_run_at + timedelta(minutes=interval_minutes)


def compute_next_run_for_simple_cron(
    *,
    cron_expression: str,
    timezone_name: str | None,
    last_run_at: datetime | None,
    reference_time: datetime | None = None,
) -> datetime:
    tz = _get_timezone(timezone_name)
    now = reference_time or utc_now()
    normalized_last_run_at = _normalize_datetime(last_run_at)
    base = normalized_last_run_at.astimezone(tz) if normalized_last_run_at is not None else now.astimezone(tz)
    next_local = croniter(cron_expression, base).get_next(datetime)
    if next_local.tzinfo is None:
        next_local = next_local.replace(tzinfo=tz)
    return next_local.astimezone(timezone.utc)


def compute_next_run_at(
    *,
    schedule_type: str,
    cron_expression: str | None,
    interval_minutes: int | None,
    timezone_name: str | None,
    last_run_at: datetime | None,
    reference_time: datetime | None = None,
) -> datetime:
    validate_schedule_type_fields(
        schedule_type=schedule_type,
        cron_expression=cron_expression,
        interval_minutes=interval_minutes,
        timezone_name=timezone_name,
    )
    if schedule_type == "interval":
        return compute_next_run_for_interval(
            interval_minutes=interval_minutes or 1,
            last_run_at=last_run_at,
            reference_time=reference_time,
        )
    return compute_next_run_for_simple_cron(
        cron_expression=cron_expression or "* * * * *",
        timezone_name=timezone_name,
        last_run_at=last_run_at,
        reference_time=reference_time,
    )


def _policy_allows_job_type(job_type: str, policy: AutomationPolicyConfig) -> bool:
    if job_type == "generate_story_ideas":
        return policy.allow_auto_generate_ideas
    if job_type == "generate_story_draft":
        return policy.allow_auto_generate_drafts
    if job_type == "generate_illustration_plan":
        return policy.allow_auto_generate_illustration_plans
    if job_type == "generate_page_illustrations":
        return policy.allow_auto_generate_page_illustrations
    if job_type == "assemble_book":
        return policy.allow_auto_assemble_books
    if job_type == "full_story_pipeline":
        return policy.allow_auto_generate_ideas or policy.allow_auto_generate_drafts
    return False


def enforce_policy_on_payload(
    *,
    job_type: str,
    payload: dict[str, Any],
    policy: AutomationPolicyConfig,
) -> tuple[dict[str, Any] | None, str, str]:
    if not _policy_allows_job_type(job_type, policy):
        return None, "skipped", "Automation policy does not allow this job type."

    adjusted = dict(payload)

    if job_type == "assemble_book":
        adjusted["publish_immediately"] = bool(adjusted.get("publish_immediately", False) and policy.allow_auto_publish)
        return adjusted, "queued", "Automation schedule queued a book assembly job."

    if job_type == "full_story_pipeline":
        if policy.stop_at_review_gate:
            adjusted["stop_at_review_gate"] = True
            adjusted["publish_immediately"] = False
            adjusted["auto_approve_illustrations"] = False
            adjusted["generate_mock_illustrations"] = False
            return adjusted, "queued", "Automation schedule queued a full pipeline job that stops at review gates."
        if not policy.allow_auto_generate_illustration_plans or not policy.allow_auto_assemble_books:
            return None, "skipped", "Policy does not allow post-review illustration planning and book assembly."
        if not policy.allow_auto_generate_page_illustrations:
            adjusted["generate_mock_illustrations"] = False
        adjusted["publish_immediately"] = bool(adjusted.get("publish_immediately", False) and policy.allow_auto_publish)
        adjusted["auto_approve_illustrations"] = False
        return adjusted, "queued", "Automation schedule queued a full pipeline job."

    return adjusted, "queued", f"Automation schedule queued a {job_type} job."


def _validate_schedule_name_uniqueness(session: Session, name: str, schedule_id: int | None = None) -> None:
    existing = session.exec(select(AutomationSchedule).where(AutomationSchedule.name == name)).first()
    if existing is not None and existing.id != schedule_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Automation schedule name already exists")


def _validate_schedule_configuration(
    *,
    session: Session,
    name: str,
    schedule_type: str,
    cron_expression: str | None,
    interval_minutes: int | None,
    timezone_name: str | None,
    job_type: str,
    payload_json: str,
    policy: AutomationPolicyConfig,
    schedule_id: int | None = None,
) -> dict[str, Any]:
    _validate_schedule_name_uniqueness(session, name, schedule_id)
    _validate_job_type(job_type)
    validate_schedule_type_fields(
        schedule_type=schedule_type,
        cron_expression=cron_expression,
        interval_minutes=interval_minutes,
        timezone_name=timezone_name,
    )
    payload = _deserialize_json(payload_json)
    if job_type in {"generate_illustration_plan", "generate_page_illustrations", "assemble_book"} and not _policy_allows_job_type(job_type, policy):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automation policy does not allow this scheduled job type.",
        )
    return payload


def get_automation_schedule_or_404(session: Session, schedule_id: int) -> AutomationSchedule:
    schedule = session.get(AutomationSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation schedule not found")
    return schedule


def list_automation_schedules(
    session: Session,
    *,
    is_active: bool | None,
    job_type: str | None,
    limit: int,
) -> list[AutomationSchedule]:
    statement = select(AutomationSchedule).order_by(AutomationSchedule.created_at.desc()).limit(limit)
    if is_active is not None:
        statement = statement.where(AutomationSchedule.is_active == is_active)
    if job_type is not None:
        _validate_job_type(job_type)
        statement = statement.where(AutomationSchedule.job_type == job_type)
    return list(session.exec(statement).all())


def get_due_schedules(session: Session, *, now: datetime | None = None, limit: int = 100) -> list[AutomationSchedule]:
    reference_time = now or utc_now()
    statement = (
        select(AutomationSchedule)
        .where(
            AutomationSchedule.is_active == True,  # noqa: E712
            AutomationSchedule.next_run_at != None,  # noqa: E711
            AutomationSchedule.next_run_at <= reference_time,
        )
        .order_by(AutomationSchedule.next_run_at.asc(), AutomationSchedule.created_at.asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def automation_schedule_to_read(schedule: AutomationSchedule) -> AutomationScheduleRead:
    return AutomationScheduleRead(
        id=schedule.id,
        name=schedule.name,
        schedule_type=schedule.schedule_type,
        cron_expression=schedule.cron_expression,
        interval_minutes=schedule.interval_minutes,
        timezone=schedule.timezone,
        job_type=schedule.job_type,
        payload_json=schedule.payload_json,
        policy_json=schedule.policy_json,
        policy=parse_policy(schedule.policy_json),
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        last_job_id=schedule.last_job_id,
        last_run_status=schedule.last_run_status,
        created_by_user_id=schedule.created_by_user_id,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


def _persist_schedule(session: Session, schedule: AutomationSchedule) -> AutomationSchedule:
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def create_schedule(
    session: Session,
    *,
    payload: AutomationScheduleCreate,
    created_by_user_id: int | None,
    actor_user: User | None = None,
    request_id: str | None = None,
) -> AutomationSchedule:
    policy = payload.policy or AutomationPolicyConfig()
    _validate_schedule_configuration(
        session=session,
        name=payload.name,
        schedule_type=payload.schedule_type,
        cron_expression=payload.cron_expression,
        interval_minutes=payload.interval_minutes,
        timezone_name=payload.timezone,
        job_type=payload.job_type,
        payload_json=payload.payload_json,
        policy=policy,
    )
    schedule = AutomationSchedule(
        name=payload.name,
        schedule_type=payload.schedule_type,
        cron_expression=payload.cron_expression,
        interval_minutes=payload.interval_minutes,
        timezone=payload.timezone or DEFAULT_AUTOMATION_TIMEZONE,
        job_type=payload.job_type,
        payload_json=payload.payload_json,
        policy_json=_serialize_policy(policy),
        is_active=payload.is_active,
        next_run_at=(
            compute_next_run_at(
                schedule_type=payload.schedule_type,
                cron_expression=payload.cron_expression,
                interval_minutes=payload.interval_minutes,
                timezone_name=payload.timezone or DEFAULT_AUTOMATION_TIMEZONE,
                last_run_at=None,
            )
            if payload.is_active
            else None
        ),
        created_by_user_id=created_by_user_id,
    )
    schedule = _persist_schedule(session, schedule)
    create_audit_log(
        session,
        action_type="automation_schedule_created",
        entity_type="automation_schedule",
        entity_id=str(schedule.id),
        summary=f"Created automation schedule '{schedule.name}'",
        actor_user=actor_user,
        request_id=request_id,
        metadata={"job_type": schedule.job_type, "schedule_type": schedule.schedule_type, "is_active": schedule.is_active},
    )
    return schedule


def update_schedule(
    session: Session,
    *,
    schedule: AutomationSchedule,
    payload: AutomationScheduleUpdate,
    actor_user: User | None = None,
    request_id: str | None = None,
) -> AutomationSchedule:
    current_policy = parse_policy(schedule.policy_json)
    updated_policy = parse_policy(payload.policy_json) if payload.policy_json is not None else current_policy
    updated_name = payload.name if payload.name is not None else schedule.name
    updated_schedule_type = payload.schedule_type if payload.schedule_type is not None else schedule.schedule_type
    updated_cron = payload.cron_expression if payload.cron_expression is not None else schedule.cron_expression
    updated_interval = payload.interval_minutes if payload.interval_minutes is not None else schedule.interval_minutes
    updated_timezone = payload.timezone if payload.timezone is not None else schedule.timezone
    updated_job_type = payload.job_type if payload.job_type is not None else schedule.job_type
    updated_payload_json = payload.payload_json if payload.payload_json is not None else schedule.payload_json
    updated_is_active = payload.is_active if payload.is_active is not None else schedule.is_active
    was_active = schedule.is_active

    _validate_schedule_configuration(
        session=session,
        name=updated_name,
        schedule_type=updated_schedule_type,
        cron_expression=updated_cron,
        interval_minutes=updated_interval,
        timezone_name=updated_timezone,
        job_type=updated_job_type,
        payload_json=updated_payload_json,
        policy=updated_policy,
        schedule_id=schedule.id,
    )

    timing_changed = any(
        value is not None
        for value in (
            payload.schedule_type,
            payload.cron_expression,
            payload.interval_minutes,
            payload.timezone,
        )
    )

    schedule.name = updated_name
    schedule.schedule_type = updated_schedule_type
    schedule.cron_expression = updated_cron
    schedule.interval_minutes = updated_interval
    schedule.timezone = updated_timezone or DEFAULT_AUTOMATION_TIMEZONE
    schedule.job_type = updated_job_type
    schedule.payload_json = updated_payload_json
    schedule.policy_json = _serialize_policy(updated_policy)
    schedule.is_active = updated_is_active
    schedule.last_run_status = _validate_last_run_status(schedule.last_run_status)
    if payload.next_run_at is not None:
        schedule.next_run_at = payload.next_run_at
    elif not schedule.is_active:
        schedule.next_run_at = None
    elif timing_changed or (not was_active and schedule.is_active) or schedule.next_run_at is None:
        schedule.next_run_at = compute_next_run_at(
            schedule_type=schedule.schedule_type,
            cron_expression=schedule.cron_expression,
            interval_minutes=schedule.interval_minutes,
            timezone_name=schedule.timezone,
            last_run_at=schedule.last_run_at,
        )
    schedule.updated_at = utc_now()
    schedule = _persist_schedule(session, schedule)
    create_audit_log(
        session,
        action_type="automation_schedule_updated",
        entity_type="automation_schedule",
        entity_id=str(schedule.id),
        summary=f"Updated automation schedule '{schedule.name}'",
        actor_user=actor_user,
        request_id=request_id,
        metadata={"job_type": schedule.job_type, "is_active": schedule.is_active},
    )
    return schedule


def activate_schedule(
    session: Session,
    *,
    schedule: AutomationSchedule,
    actor_user: User | None = None,
    request_id: str | None = None,
) -> AutomationSchedule:
    schedule.is_active = True
    schedule.next_run_at = compute_next_run_at(
        schedule_type=schedule.schedule_type,
        cron_expression=schedule.cron_expression,
        interval_minutes=schedule.interval_minutes,
        timezone_name=schedule.timezone,
        last_run_at=schedule.last_run_at,
    )
    schedule.updated_at = utc_now()
    schedule = _persist_schedule(session, schedule)
    create_audit_log(
        session,
        action_type="automation_schedule_activated",
        entity_type="automation_schedule",
        entity_id=str(schedule.id),
        summary=f"Activated automation schedule '{schedule.name}'",
        actor_user=actor_user,
        request_id=request_id,
        metadata={"next_run_at": schedule.next_run_at},
    )
    return schedule


def deactivate_schedule(
    session: Session,
    *,
    schedule: AutomationSchedule,
    actor_user: User | None = None,
    request_id: str | None = None,
) -> AutomationSchedule:
    schedule.is_active = False
    schedule.next_run_at = None
    schedule.updated_at = utc_now()
    schedule = _persist_schedule(session, schedule)
    create_audit_log(
        session,
        action_type="automation_schedule_deactivated",
        entity_type="automation_schedule",
        entity_id=str(schedule.id),
        summary=f"Deactivated automation schedule '{schedule.name}'",
        actor_user=actor_user,
        request_id=request_id,
        metadata=None,
    )
    return schedule


def delete_schedule(
    session: Session,
    *,
    schedule: AutomationSchedule,
    actor_user: User | None = None,
    request_id: str | None = None,
) -> None:
    schedule_id = schedule.id
    schedule_name = schedule.name
    session.delete(schedule)
    session.commit()
    create_audit_log(
        session,
        action_type="automation_schedule_deleted",
        entity_type="automation_schedule",
        entity_id=str(schedule_id),
        summary=f"Deleted automation schedule '{schedule_name}'",
        actor_user=actor_user,
        request_id=request_id,
        metadata=None,
    )


def should_skip_schedule(schedule: AutomationSchedule, *, now: datetime | None = None, force: bool = False) -> bool:
    reference_time = now or utc_now()
    next_run_at = _normalize_datetime(schedule.next_run_at)
    if not schedule.is_active and not force:
        return True
    if force:
        return False
    return next_run_at is None or next_run_at > reference_time


def _update_schedule_after_run(
    session: Session,
    *,
    schedule: AutomationSchedule,
    last_job_id: int | None,
    last_run_status: str,
    reference_time: datetime,
) -> AutomationSchedule:
    schedule.last_run_at = reference_time
    schedule.last_job_id = last_job_id
    schedule.last_run_status = _validate_last_run_status(last_run_status)
    schedule.next_run_at = (
        compute_next_run_at(
            schedule_type=schedule.schedule_type,
            cron_expression=schedule.cron_expression,
            interval_minutes=schedule.interval_minutes,
            timezone_name=schedule.timezone,
            last_run_at=reference_time,
            reference_time=reference_time,
        )
        if schedule.is_active
        else None
    )
    schedule.updated_at = reference_time
    return _persist_schedule(session, schedule)


def run_schedule(
    session: Session,
    *,
    schedule: AutomationSchedule,
    background_tasks: BackgroundTasks | None = None,
    actor_user: User | None = None,
    request_id: str | None = None,
    force: bool = False,
) -> AutomationScheduleRunResponse:
    now = utc_now()
    if should_skip_schedule(schedule, now=now, force=force):
        schedule = _update_schedule_after_run(
            session,
            schedule=schedule,
            last_job_id=None,
            last_run_status="skipped",
            reference_time=now,
        )
        message = "Schedule is not active or not yet due."
        create_audit_log(
            session,
            action_type="automation_schedule_skipped",
            entity_type="automation_schedule",
            entity_id=str(schedule.id),
            summary=f"Skipped automation schedule '{schedule.name}'",
            actor_user=actor_user,
            request_id=request_id,
            metadata={"reason": message},
        )
        return AutomationScheduleRunResponse(
            schedule=automation_schedule_to_read(schedule),
            queued_job_id=None,
            action="skipped",
            message=message,
        )

    policy = parse_policy(schedule.policy_json)
    raw_payload = _deserialize_json(schedule.payload_json)
    adjusted_payload, action, message = enforce_policy_on_payload(
        job_type=schedule.job_type,
        payload=raw_payload,
        policy=policy,
    )
    if adjusted_payload is None:
        schedule = _update_schedule_after_run(
            session,
            schedule=schedule,
            last_job_id=None,
            last_run_status="skipped",
            reference_time=now,
        )
        create_audit_log(
            session,
            action_type="automation_schedule_skipped",
            entity_type="automation_schedule",
            entity_id=str(schedule.id),
            summary=f"Skipped automation schedule '{schedule.name}'",
            actor_user=actor_user,
            request_id=request_id,
            metadata={"reason": message},
        )
        return AutomationScheduleRunResponse(
            schedule=automation_schedule_to_read(schedule),
            queued_job_id=None,
            action=action,
            message=message,
        )

    try:
        job = create_job(
            session,
            job_type=schedule.job_type,
            payload_json=_serialize_json(adjusted_payload),
            created_by_user_id=schedule.created_by_user_id,
            request_id=request_id,
        )
        if background_tasks is not None:
            background_tasks.add_task(
                run_job_by_id,
                job.id,
                actor_user_id=schedule.created_by_user_id,
                request_id=request_id,
            )
        schedule = _update_schedule_after_run(
            session,
            schedule=schedule,
            last_job_id=job.id,
            last_run_status="succeeded",
            reference_time=now,
        )
        create_audit_log(
            session,
            action_type="automation_schedule_run",
            entity_type="automation_schedule",
            entity_id=str(schedule.id),
            summary=f"Ran automation schedule '{schedule.name}'",
            actor_user=actor_user,
            request_id=request_id,
            metadata={"job_id": job.id, "job_type": schedule.job_type, "action": action},
        )
        return AutomationScheduleRunResponse(
            schedule=automation_schedule_to_read(schedule),
            queued_job_id=job.id,
            action=action,
            message=message,
        )
    except Exception as exc:
        schedule = _update_schedule_after_run(
            session,
            schedule=schedule,
            last_job_id=None,
            last_run_status="failed",
            reference_time=now,
        )
        create_audit_log(
            session,
            action_type="automation_schedule_run",
            entity_type="automation_schedule",
            entity_id=str(schedule.id),
            summary=f"Automation schedule '{schedule.name}' failed to queue a workflow job",
            actor_user=actor_user,
            request_id=request_id,
            metadata={"error": str(exc)},
        )
        return AutomationScheduleRunResponse(
            schedule=automation_schedule_to_read(schedule),
            queued_job_id=None,
            action="failed",
            message=str(exc),
        )


def run_due_schedules(
    session: Session,
    *,
    limit: int,
    background_tasks: BackgroundTasks | None = None,
    actor_user: User | None = None,
    request_id: str | None = None,
) -> list[AutomationScheduleRunResponse]:
    schedules = get_due_schedules(session, limit=limit)
    return [
        run_schedule(
            session,
            schedule=schedule,
            background_tasks=background_tasks,
            actor_user=actor_user,
            request_id=request_id,
            force=False,
        )
        for schedule in schedules
    ]
