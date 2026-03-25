from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlmodel import Session, select

from app.models import (
    Book,
    ChildProfile,
    MaintenanceJob,
    StoryDraft,
    StoryIdea,
    User,
    UserLibraryItem,
)
from app.models.user import utc_now
from app.services.account_health_service import rebuild_account_health_snapshot
from app.services.child_profile_service import rebuild_child_reading_profile
from app.services.discovery_service import rebuild_all_discovery_metadata, rebuild_book_discovery_metadata
from app.services.feedback_service import rebuild_user_story_profile
from app.services.library_service import build_book_download_package, get_active_package_for_book
from app.services.reengagement_service import generate_reengagement_suggestions, rebuild_user_engagement_state
from app.services.user_service import get_user_by_id

MAINTENANCE_JOB_TYPES = {
    "rebuild_discovery_metadata",
    "rebuild_recommendation_data",
    "rebuild_child_profiles",
    "rebuild_account_health",
    "rebuild_reengagement",
    "backfill_content_lane_keys",
    "repair_download_packages",
    "custom",
}
MAINTENANCE_JOB_STATUSES = {"pending", "running", "succeeded", "failed", "canceled"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _normalize_json_string(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON payload: {exc.msg}") from exc
    return json.dumps(parsed, default=str, sort_keys=True)


def _serialize_result(value: dict[str, Any]) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    return str(exc)


def validate_job_type(job_type: str) -> str:
    if job_type not in MAINTENANCE_JOB_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid maintenance job type")
    return job_type


def validate_job_status(status_value: str) -> str:
    if status_value not in MAINTENANCE_JOB_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid maintenance job status")
    return status_value


def get_maintenance_job_or_404(session: Session, *, job_id: int) -> MaintenanceJob:
    job = session.get(MaintenanceJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance job not found")
    return job


def list_maintenance_jobs(
    session: Session,
    *,
    status_value: str | None,
    job_type: str | None,
    limit: int,
) -> list[MaintenanceJob]:
    statement = select(MaintenanceJob).order_by(MaintenanceJob.created_at.desc()).limit(limit)
    if status_value is not None:
        statement = statement.where(MaintenanceJob.status == validate_job_status(status_value))
    if job_type is not None:
        statement = statement.where(MaintenanceJob.job_type == validate_job_type(job_type))
    return list(session.exec(statement).all())


def create_maintenance_job(
    session: Session,
    *,
    key: str,
    title: str,
    description: str | None,
    job_type: str,
    target_scope: str | None,
    parameters_json: str | None,
    created_by_user_id: int | None,
) -> MaintenanceJob:
    job = MaintenanceJob(
        key=key.strip(),
        title=title.strip(),
        description=description.strip() if description is not None and description.strip() else None,
        job_type=validate_job_type(job_type),
        status="pending",
        target_scope=target_scope.strip() if target_scope is not None and target_scope.strip() else None,
        parameters_json=_normalize_json_string(parameters_json),
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, job)


def update_maintenance_job(
    session: Session,
    *,
    job: MaintenanceJob,
    status_value: str | None = None,
    result_json: str | None = None,
    error_message: str | None = None,
    started_at=None,
    completed_at=None,
    result_json_provided: bool = False,
    error_message_provided: bool = False,
    started_at_provided: bool = False,
    completed_at_provided: bool = False,
) -> MaintenanceJob:
    if status_value is not None:
        job.status = validate_job_status(status_value)
    if result_json_provided:
        job.result_json = _normalize_json_string(result_json)
    if error_message_provided:
        job.error_message = error_message.strip() if error_message is not None and error_message.strip() else None
    if started_at_provided:
        job.started_at = started_at
    if completed_at_provided:
        job.completed_at = completed_at
    job.updated_at = utc_now()
    return _persist(session, job)


def cancel_maintenance_job(session: Session, *, job: MaintenanceJob) -> MaintenanceJob:
    if job.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending maintenance jobs can be canceled")
    job.status = "canceled"
    job.completed_at = utc_now()
    job.updated_at = utc_now()
    return _persist(session, job)


def _parse_scope_id(target_scope: str | None, *, prefix: str) -> int | None:
    if target_scope is None or not target_scope.strip() or target_scope == "all":
        return None
    normalized = target_scope.strip()
    if not normalized.startswith(f"{prefix}:"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid target scope for {prefix}")
    _, _, raw_id = normalized.partition(":")
    try:
        return int(raw_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {prefix} target scope") from exc


def _scope_label(scope_id: int | None, *, prefix: str) -> str:
    return "all" if scope_id is None else f"{prefix}:{scope_id}"


def _infer_content_lane_key(age_band: str | None) -> str | None:
    if age_band == "3-7":
        return "bedtime_3_7"
    if age_band == "8-12":
        return "story_adventures_3_7"
    return None


def handle_rebuild_discovery_metadata(session: Session, *, target_scope: str | None) -> dict[str, Any]:
    book_id = _parse_scope_id(target_scope, prefix="book")
    if book_id is None:
        items = rebuild_all_discovery_metadata(session)
        return {
            "scope": "all",
            "processed_count": len(items),
            "updated_count": len(items),
            "skipped_count": 0,
        }
    rebuild_book_discovery_metadata(session, book_id=book_id)
    return {
        "scope": _scope_label(book_id, prefix="book"),
        "processed_count": 1,
        "updated_count": 1,
        "skipped_count": 0,
    }


def handle_rebuild_recommendation_data(session: Session, *, target_scope: str | None) -> dict[str, Any]:
    user_id = _parse_scope_id(target_scope, prefix="user")
    users = [get_user_by_id(session, user_id)] if user_id is not None else list(session.exec(select(User).order_by(User.created_at.asc())).all())
    if user_id is not None and users[0] is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    processed_count = 0
    for user in users:
        if user is None:
            continue
        rebuild_user_story_profile(session, user_id=user.id)
        processed_count += 1
    return {
        "scope": _scope_label(user_id, prefix="user"),
        "processed_count": processed_count,
        "updated_count": processed_count,
        "skipped_count": 0,
    }


def handle_rebuild_child_profiles(session: Session, *, target_scope: str | None) -> dict[str, Any]:
    child_id = _parse_scope_id(target_scope, prefix="child")
    child_profiles = [session.get(ChildProfile, child_id)] if child_id is not None else list(
        session.exec(select(ChildProfile).order_by(ChildProfile.created_at.asc())).all()
    )
    if child_id is not None and child_profiles[0] is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child profile not found")
    processed_count = 0
    for child_profile in child_profiles:
        if child_profile is None:
            continue
        rebuild_child_reading_profile(session, child_profile=child_profile)
        processed_count += 1
    return {
        "scope": _scope_label(child_id, prefix="child"),
        "processed_count": processed_count,
        "updated_count": processed_count,
        "skipped_count": 0,
    }


def handle_rebuild_account_health(session: Session, *, target_scope: str | None) -> dict[str, Any]:
    user_id = _parse_scope_id(target_scope, prefix="user")
    users = [get_user_by_id(session, user_id)] if user_id is not None else list(session.exec(select(User).order_by(User.created_at.asc())).all())
    if user_id is not None and users[0] is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    processed_count = 0
    for user in users:
        if user is None:
            continue
        rebuild_account_health_snapshot(session, user=user)
        processed_count += 1
    return {
        "scope": _scope_label(user_id, prefix="user"),
        "processed_count": processed_count,
        "updated_count": processed_count,
        "skipped_count": 0,
    }


def handle_rebuild_reengagement(session: Session, *, target_scope: str | None) -> dict[str, Any]:
    user_id = _parse_scope_id(target_scope, prefix="user")
    users = [get_user_by_id(session, user_id)] if user_id is not None else list(session.exec(select(User).order_by(User.created_at.asc())).all())
    if user_id is not None and users[0] is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    processed_count = 0
    suggestion_count = 0
    for user in users:
        if user is None:
            continue
        state = rebuild_user_engagement_state(session, user=user)
        suggestions = generate_reengagement_suggestions(session, user=user, engagement_state=state)
        processed_count += 1
        suggestion_count += len(suggestions)
    return {
        "scope": _scope_label(user_id, prefix="user"),
        "processed_count": processed_count,
        "updated_count": processed_count,
        "skipped_count": 0,
        "suggestion_count": suggestion_count,
    }


def handle_backfill_content_lane_keys(session: Session, *, target_scope: str | None) -> dict[str, Any]:
    if target_scope is not None and target_scope not in {"all", ""}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="backfill_content_lane_keys only supports target scope 'all'")
    story_ideas = list(session.exec(select(StoryIdea).order_by(StoryIdea.created_at.asc())).all())
    story_drafts = list(session.exec(select(StoryDraft).order_by(StoryDraft.created_at.asc())).all())
    books = list(session.exec(select(Book).order_by(Book.created_at.asc())).all())
    processed_count = 0
    updated_count = 0
    skipped_count = 0
    model_updates = {"story_ideas": 0, "story_drafts": 0, "books": 0}
    for collection_name, rows in (
        ("story_ideas", story_ideas),
        ("story_drafts", story_drafts),
        ("books", books),
    ):
        for row in rows:
            processed_count += 1
            if row.content_lane_key:
                skipped_count += 1
                continue
            inferred = _infer_content_lane_key(row.age_band)
            if inferred is None:
                skipped_count += 1
                continue
            row.content_lane_key = inferred
            row.updated_at = utc_now()
            session.add(row)
            updated_count += 1
            model_updates[collection_name] += 1
    session.commit()
    return {
        "scope": "all",
        "processed_count": processed_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        **model_updates,
    }


def handle_repair_download_packages(session: Session, *, target_scope: str | None) -> dict[str, Any]:
    book_id = _parse_scope_id(target_scope, prefix="book")
    if book_id is None:
        used_book_ids = {
            item.book_id
            for item in session.exec(
                select(UserLibraryItem).where(
                    or_(
                        UserLibraryItem.saved_for_offline.is_(True),
                        UserLibraryItem.downloaded_at.is_not(None),
                    )
                )
            ).all()
        }
        candidate_books = list(session.exec(select(Book).where(Book.id.in_(used_book_ids)).order_by(Book.created_at.asc())).all()) if used_book_ids else []
    else:
        book = session.get(Book, book_id)
        if book is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        candidate_books = [book]
    processed_count = 0
    updated_count = 0
    skipped_count = 0
    for book in candidate_books:
        processed_count += 1
        existing = get_active_package_for_book(session, book_id=book.id, language=book.language)
        if existing is not None:
            skipped_count += 1
            continue
        build_book_download_package(session, book_id=book.id, language=book.language, replace_existing=True)
        updated_count += 1
    return {
        "scope": _scope_label(book_id, prefix="book"),
        "processed_count": processed_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
    }


def _dispatch_job(session: Session, *, job: MaintenanceJob) -> dict[str, Any]:
    if job.job_type == "rebuild_discovery_metadata":
        return handle_rebuild_discovery_metadata(session, target_scope=job.target_scope)
    if job.job_type == "rebuild_recommendation_data":
        return handle_rebuild_recommendation_data(session, target_scope=job.target_scope)
    if job.job_type == "rebuild_child_profiles":
        return handle_rebuild_child_profiles(session, target_scope=job.target_scope)
    if job.job_type == "rebuild_account_health":
        return handle_rebuild_account_health(session, target_scope=job.target_scope)
    if job.job_type == "rebuild_reengagement":
        return handle_rebuild_reengagement(session, target_scope=job.target_scope)
    if job.job_type == "backfill_content_lane_keys":
        return handle_backfill_content_lane_keys(session, target_scope=job.target_scope)
    if job.job_type == "repair_download_packages":
        return handle_repair_download_packages(session, target_scope=job.target_scope)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This maintenance job type is not runnable through the API")


def run_maintenance_job(session: Session, *, job: MaintenanceJob) -> MaintenanceJob:
    if job.status not in {"pending", "failed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending or failed maintenance jobs can be run")
    job.status = "running"
    job.started_at = utc_now()
    job.completed_at = None
    job.result_json = None
    job.error_message = None
    job.updated_at = utc_now()
    job = _persist(session, job)
    try:
        result = _dispatch_job(session, job=job)
        job.status = "succeeded"
        job.result_json = _serialize_result(result)
        job.error_message = None
        job.completed_at = utc_now()
        job.updated_at = utc_now()
        return _persist(session, job)
    except Exception as exc:
        session.rollback()
        failed_job = get_maintenance_job_or_404(session, job_id=job.id)
        failed_job.status = "failed"
        failed_job.error_message = _error_message(exc)
        failed_job.completed_at = utc_now()
        failed_job.updated_at = utc_now()
        return _persist(session, failed_job)
