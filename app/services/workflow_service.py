from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from fastapi import BackgroundTasks, HTTPException, status
from sqlmodel import Session, select

from app.config import ILLUSTRATION_GENERATION_PROVIDER
from app.database import engine
from app.models import Character, Illustration, StoryDraft, StoryIdea, StoryPage, User, WorkflowJob
from app.services.audit_service import create_audit_log
from app.services.book_builder import assemble_book_from_draft
from app.services.content_lane_service import validate_content_lane_key
from app.services.idea_generator import generate_story_idea_payloads
from app.services.illustration_generator import approve_illustration, generate_illustration_asset
from app.services.illustration_planner import generate_story_page_payloads
from app.services.narration_service import generate_book_narration
from app.services.notification_service import generate_daily_story_suggestion
from app.services.quality_service import run_story_draft_quality_checks, run_story_pages_quality_checks
from app.services.review_service import approve_story_draft, utc_now
from app.services.story_brief_service import upsert_story_brief_record
from app.services.story_review_queue_service import upsert_story_review_queue_item
from app.services.story_writer import generate_story_draft_payload
from app.services.story_quality_service import evaluate_illustration_quality, evaluate_story_quality
from app.services.story_suggestion_service import (
    build_story_suggestion_guidance_lines,
    list_story_suggestion_references,
)

WORKFLOW_JOB_STATUSES = {"queued", "running", "succeeded", "failed", "canceled"}
WORKFLOW_JOB_TYPES = {
    "generate_story_ideas",
    "generate_story_draft",
    "generate_illustration_plan",
    "generate_page_illustrations",
    "assemble_book",
    "generate_book_narration",
    "generate_daily_story_suggestion",
    "full_story_pipeline",
}


def _serialize_json(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _deserialize_json(value: str) -> dict[str, Any]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payload_json: {exc.msg}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow job payload must be a JSON object")
    return data


def _get_actor_user(session: Session, actor_user_id: int | None) -> User | None:
    if actor_user_id is None:
        return None
    return session.get(User, actor_user_id)


def _validate_job_type(job_type: str) -> str:
    if job_type not in WORKFLOW_JOB_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow job type")
    return job_type


def _validate_job_status(status_value: str) -> str:
    if status_value not in WORKFLOW_JOB_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow job status")
    return status_value


def _persist_job(session: Session, job: WorkflowJob) -> WorkflowJob:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_workflow_job_or_404(session: Session, job_id: int) -> WorkflowJob:
    job = session.get(WorkflowJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow job not found")
    return job


def list_workflow_jobs(
    session: Session,
    *,
    status_value: str | None,
    job_type: str | None,
    created_by_user_id: int | None,
    limit: int,
) -> list[WorkflowJob]:
    statement = select(WorkflowJob).order_by(WorkflowJob.created_at.desc()).limit(limit)
    if status_value:
        _validate_job_status(status_value)
        statement = statement.where(WorkflowJob.status == status_value)
    if job_type:
        _validate_job_type(job_type)
        statement = statement.where(WorkflowJob.job_type == job_type)
    if created_by_user_id is not None:
        statement = statement.where(WorkflowJob.created_by_user_id == created_by_user_id)
    return list(session.exec(statement).all())


def create_job(
    session: Session,
    *,
    job_type: str,
    payload_json: str,
    created_by_user_id: int | None,
    priority: int = 5,
    scheduled_for: datetime | None = None,
    max_attempts: int = 1,
    parent_job_id: int | None = None,
    request_id: str | None = None,
) -> WorkflowJob:
    _validate_job_type(job_type)
    _deserialize_json(payload_json)
    if max_attempts < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="max_attempts must be at least 1")
    job = WorkflowJob(
        job_type=job_type,
        status="queued",
        priority=priority,
        payload_json=payload_json,
        created_by_user_id=created_by_user_id,
        scheduled_for=scheduled_for,
        max_attempts=max_attempts,
        parent_job_id=parent_job_id,
    )
    job = _persist_job(session, job)
    create_audit_log(
        session,
        action_type="workflow_job_created",
        entity_type="workflow_job",
        entity_id=str(job.id),
        summary=f"Created workflow job {job.id} ({job.job_type})",
        actor_user=_get_actor_user(session, created_by_user_id),
        request_id=request_id,
        metadata={"job_type": job.job_type, "priority": job.priority},
    )
    return job


def cancel_job(
    session: Session,
    *,
    job: WorkflowJob,
    actor_user_id: int | None = None,
    request_id: str | None = None,
) -> WorkflowJob:
    if job.status != "queued":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only queued jobs can be canceled")
    job.status = "canceled"
    job.completed_at = utc_now()
    job.updated_at = utc_now()
    job = _persist_job(session, job)
    create_audit_log(
        session,
        action_type="workflow_job_canceled",
        entity_type="workflow_job",
        entity_id=str(job.id),
        summary=f"Canceled workflow job {job.id} ({job.job_type})",
        actor_user=_get_actor_user(session, actor_user_id),
        request_id=request_id,
        metadata={"job_type": job.job_type},
    )
    return job


def get_job_result(job: WorkflowJob) -> dict[str, Any] | None:
    if not job.result_json:
        return None
    return _deserialize_json(job.result_json)


def _active_character_names(session: Session) -> list[str]:
    return list(
        session.exec(select(Character.name).where(Character.is_active.is_(True)).order_by(Character.name)).all()
    )


def _quality_status_from_checks(checks: list[Any]) -> str:
    if any(check.status == "failed" for check in checks):
        return "failed"
    if any(check.status == "warning" for check in checks):
        return "warning"
    return "passed"


def _safe_run_draft_quality_checks(
    session: Session,
    *,
    story_draft_id: int,
    created_by_job_id: int | None,
) -> dict[str, Any]:
    try:
        checks = run_story_draft_quality_checks(session, story_draft_id=story_draft_id, created_by_job_id=created_by_job_id)
        return {
            "target_type": "story_draft",
            "target_id": story_draft_id,
            "overall_status": _quality_status_from_checks(checks),
            "check_count": len(checks),
        }
    except Exception as exc:
        return {
            "target_type": "story_draft",
            "target_id": story_draft_id,
            "overall_status": "error",
            "detail": str(exc),
        }


def _safe_run_story_pages_quality_checks(
    session: Session,
    *,
    story_draft_id: int,
    created_by_job_id: int | None,
) -> dict[str, Any]:
    try:
        checks = run_story_pages_quality_checks(session, story_draft_id=story_draft_id, created_by_job_id=created_by_job_id)
        return {
            "target_type": "story_pages",
            "target_id": story_draft_id,
            "overall_status": _quality_status_from_checks(checks),
            "check_count": len(checks),
        }
    except Exception as exc:
        return {
            "target_type": "story_pages",
            "target_id": story_draft_id,
            "overall_status": "error",
            "detail": str(exc),
        }


def _queue_status_for_review_status(review_status: str) -> str:
    return {
        "draft_pending_review": "pending_review",
        "review_pending": "pending_review",
        "needs_revision": "needs_edit",
        "approved_for_illustration": "approved",
        "rejected": "rejected",
    }.get(review_status, "pending_review")


def handle_generate_story_ideas(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    lane = validate_content_lane_key(
        session,
        age_band=payload.get("age_band", "3-7"),
        content_lane_key=payload.get("content_lane_key"),
    )
    available_characters = _active_character_names(session)
    recent_premises = session.exec(
        select(StoryIdea.premise).order_by(StoryIdea.created_at.desc()).limit(120),
    ).all()
    seen_keys: set[str] = set()
    exclude_set: set[str] = set()
    hint_lines: list[str] = []
    for p in recent_premises:
        s = str(p).strip()
        if not s:
            continue
        key = s.casefold()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        exclude_set.add(key)
        hint_lines.append(s[:240])
        if len(hint_lines) >= 35:
            break
    suggestion_references = list_story_suggestion_references(
        session,
        age_band=lane.age_band,
        limit=3,
    )
    suggestion_guidance = tuple(build_story_suggestion_guidance_lines(suggestion_references))
    batch = generate_story_idea_payloads(
        count=payload.get("count", 5),
        age_band=lane.age_band,
        content_lane_key=lane.key,
        tone=payload.get("tone", "calm, gentle, plot-led"),
        include_characters=payload.get("include_characters"),
        bedtime_only=payload.get("bedtime_only", True),
        available_characters=available_characters,
        exclude_premises=frozenset(exclude_set) if exclude_set else None,
        exclude_premise_hints=tuple(hint_lines) if hint_lines else None,
        editorial_guidance=suggestion_guidance or None,
    )
    created_ids: list[int] = []
    for item in batch.payloads:
        story_idea = StoryIdea(**item)
        session.add(story_idea)
        session.commit()
        session.refresh(story_idea)
        created_ids.append(story_idea.id)
    return {
        "created_count": len(created_ids),
        "story_idea_ids": created_ids,
        "approved_story_suggestion_count": len(suggestion_references),
    }


def handle_generate_story_draft(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    story_idea_id = int(payload["story_idea_id"])
    story_idea = session.get(StoryIdea, story_idea_id)
    if story_idea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story idea not found")
    generated = generate_story_draft_payload(story_idea, session=session)
    story_draft = StoryDraft(
        story_idea_id=story_idea.id,
        title=generated.title,
        age_band=story_idea.age_band,
        language="en",
        content_lane_key=generated.content_lane_key,
        full_text=generated.full_text,
        summary=generated.summary,
        read_time_minutes=generated.read_time_minutes,
        review_status=generated.review_status,
        generation_source=generated.generation_source,
    )
    session.add(story_draft)
    story_idea.status = "converted_to_draft"
    story_idea.updated_at = utc_now()
    session.add(story_idea)
    session.commit()
    session.refresh(story_draft)
    upsert_story_brief_record(
        session,
        story_idea_id=story_idea.id,
        story_brief=generated.story_brief,
    )
    upsert_story_review_queue_item(
        session,
        story_id=story_draft.id,
        generated_story=generated.generated_story,
        rewritten_story=generated.rewritten_story,
        story_brief=generated.story_brief,
        story_validation=generated.story_validation,
        outline=generated.story_outline,
        illustration_scenes=generated.illustration_scenes,
        story_metadata=generated.story_metadata,
        status=_queue_status_for_review_status(generated.review_status),
    )
    quality_summary = _safe_run_draft_quality_checks(
        session,
        story_draft_id=story_draft.id,
        created_by_job_id=payload.get("_workflow_job_id"),
    )
    auto_review = evaluate_story_quality(
        session,
        story_id=story_draft.id,
        actor_user_id=payload.get("actor_user_id"),
    )
    return {
        "story_draft_id": story_draft.id,
        "story_idea_id": story_idea.id,
        "review_status": story_draft.review_status,
        "quality_summary": quality_summary,
        "story_quality_score": auto_review.quality_score,
        "review_required": auto_review.review_required,
    }


def _delete_existing_story_pages(session: Session, story_draft_id: int) -> None:
    existing_pages = list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft_id)).all())
    for page in existing_pages:
        illustrations = list(session.exec(select(Illustration).where(Illustration.story_page_id == page.id)).all())
        for illustration in illustrations:
            session.delete(illustration)
        session.delete(page)
    session.commit()


def handle_generate_illustration_plan(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    story_draft_id = int(payload["story_draft_id"])
    story_draft = session.get(StoryDraft, story_draft_id)
    if story_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    if story_draft.review_status != "approved_for_illustration":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story draft must be approved_for_illustration before planning pages",
        )
    _delete_existing_story_pages(session, story_draft.id)
    page_payloads = generate_story_page_payloads(
        story_draft=story_draft,
        story_idea=session.get(StoryIdea, story_draft.story_idea_id) if story_draft.story_idea_id is not None else None,
        target_page_count=None,
        min_pages=int(payload.get("min_pages", 5)),
        max_pages=int(payload.get("max_pages", 6)),
    )
    created_page_ids: list[int] = []
    for item in page_payloads:
        page = StoryPage(**item)
        session.add(page)
        session.commit()
        session.refresh(page)
        created_page_ids.append(page.id)
    quality_summary = _safe_run_story_pages_quality_checks(
        session,
        story_draft_id=story_draft.id,
        created_by_job_id=payload.get("_workflow_job_id"),
    )
    return {
        "story_draft_id": story_draft.id,
        "created_count": len(created_page_ids),
        "page_ids": created_page_ids,
        "quality_summary": quality_summary,
    }


def handle_generate_page_illustrations(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    story_draft_id = int(payload["story_draft_id"])
    provider = str(payload.get("provider") or ILLUSTRATION_GENERATION_PROVIDER or "mock")
    page_statement = select(StoryPage).where(StoryPage.story_draft_id == story_draft_id).order_by(StoryPage.page_number)
    requested_page_ids = payload.get("page_ids")
    if requested_page_ids:
        page_statement = page_statement.where(StoryPage.id.in_(requested_page_ids))
    pages = list(session.exec(page_statement).all())
    if not pages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No story pages available for illustration generation")
    illustration_ids: list[int] = []
    illustration_quality_reviews: list[dict[str, object]] = []
    for page in pages:
        illustration = generate_illustration_asset(
            session,
            story_page=page,
            provider=provider,
            generation_notes="Workflow-generated illustration",
        )
        illustration_ids.append(illustration.id)
        review = evaluate_illustration_quality(
            session,
            illustration_id=illustration.id,
            actor_user_id=payload.get("actor_user_id"),
        )
        illustration_quality_reviews.append(
            {
                "illustration_id": illustration.id,
                "review_required": review.review_required,
                "style_consistency_score": review.style_consistency_score,
                "character_consistency_score": review.character_consistency_score,
                "color_palette_score": review.color_palette_score,
            }
        )
    return {
        "story_draft_id": story_draft_id,
        "generated_count": len(illustration_ids),
        "illustration_ids": illustration_ids,
        "page_ids": [page.id for page in pages],
        "provider": provider,
        "illustration_quality_reviews": illustration_quality_reviews,
    }


def handle_assemble_book(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    book, pages = assemble_book_from_draft(
        session,
        story_draft_id=int(payload["story_draft_id"]),
        language=payload.get("language", "en"),
        content_lane_key=payload.get("content_lane_key"),
        publish_immediately=bool(payload.get("publish_immediately", False)),
        replace_existing=bool(payload.get("replace_existing", True)),
    )
    return {"book_id": book.id, "page_count": len(pages), "publication_status": book.publication_status}


def handle_generate_book_narration(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    narration, segments, voice = generate_book_narration(
        session,
        book_id=int(payload["book_id"]),
        voice_key=str(payload["voice_key"]),
        language=str(payload.get("language", "en")),
        replace_existing=bool(payload.get("replace_existing", False)),
        actor_user=None,
    )
    return {
        "book_id": narration.book_id,
        "narration_id": narration.id,
        "segment_count": len(segments),
        "voice_key": voice.key,
        "language": narration.language,
    }


def handle_generate_daily_story_suggestion(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    user = session.get(User, int(payload["user_id"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    target_date = date.fromisoformat(payload["date"]) if payload.get("date") else None
    result = generate_daily_story_suggestion(
        session,
        user=user,
        child_profile_id=payload.get("child_profile_id"),
        target_date=target_date,
    )
    return {
        "user_id": user.id,
        "child_profile_id": payload.get("child_profile_id"),
        "suggestion_id": result.suggestion.id if result.suggestion is not None else None,
        "book_id": result.suggestion.book_id if result.suggestion is not None else None,
        "date": str(target_date or utc_now().date()),
    }


def _generate_single_story_idea(session: Session) -> StoryIdea:
    result = handle_generate_story_ideas(
        session,
        {"count": 1, "age_band": "3-7", "content_lane_key": None, "tone": "calm, gentle, plot-led", "bedtime_only": True},
    )
    return session.get(StoryIdea, result["story_idea_ids"][0])


def _latest_draft_for_idea(session: Session, story_idea_id: int) -> StoryDraft | None:
    return session.exec(
        select(StoryDraft)
        .where(StoryDraft.story_idea_id == story_idea_id)
        .order_by(StoryDraft.updated_at.desc())
    ).first()


def _approved_draft_for_idea(session: Session, story_idea_id: int) -> StoryDraft | None:
    return session.exec(
        select(StoryDraft)
        .where(
            StoryDraft.story_idea_id == story_idea_id,
            StoryDraft.review_status == "approved_for_illustration",
        )
        .order_by(StoryDraft.updated_at.desc())
    ).first()


def handle_full_story_pipeline(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    story_idea_id = payload.get("story_idea_id")
    if story_idea_id is None:
        if not payload.get("auto_generate_idea_if_missing", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="story_idea_id is required unless auto_generate_idea_if_missing is true",
            )
        story_idea = _generate_single_story_idea(session)
    else:
        story_idea = session.get(StoryIdea, int(story_idea_id))
        if story_idea is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story idea not found")

    approved_draft = _approved_draft_for_idea(session, story_idea.id)
    if approved_draft is None:
        draft_result = handle_generate_story_draft(
            session,
            {"story_idea_id": story_idea.id, "_workflow_job_id": payload.get("_workflow_job_id")},
        )
        latest_draft = _latest_draft_for_idea(session, story_idea.id)
        return {
            "story_idea_id": story_idea.id,
            "story_draft_id": latest_draft.id if latest_draft is not None else draft_result["story_draft_id"],
            "status": "awaiting_human_review",
            "message": "Draft generated and awaiting human review",
            "quality_summary": draft_result.get("quality_summary"),
        }
    if payload.get("stop_at_review_gate", False):
        return {
            "story_idea_id": story_idea.id,
            "story_draft_id": approved_draft.id,
            "status": "stopped_at_review_gate",
            "message": "Approved draft exists, but automation policy stopped before post-review steps",
        }

    result: dict[str, Any] = {
        "story_idea_id": story_idea.id,
        "story_draft_id": approved_draft.id,
        "status": "continued_from_review_approved_draft",
    }
    plan_result = handle_generate_illustration_plan(
        session,
        {
            "story_draft_id": approved_draft.id,
            "min_pages": 5,
            "max_pages": 6,
            "_workflow_job_id": payload.get("_workflow_job_id"),
        },
    )
    result["page_ids"] = plan_result["page_ids"]
    result["quality_summary"] = plan_result.get("quality_summary")
    if payload.get("generate_mock_illustrations", True):
        illustration_result = handle_generate_page_illustrations(
            session,
            {
                "story_draft_id": approved_draft.id,
                "page_ids": plan_result["page_ids"],
                "provider": payload.get("provider") or ILLUSTRATION_GENERATION_PROVIDER,
            },
        )
        result["illustration_ids"] = illustration_result["illustration_ids"]
        if payload.get("auto_approve_illustrations", False):
            approved_illustration_ids: list[int] = []
            for illustration_id in illustration_result["illustration_ids"]:
                illustration = session.get(Illustration, illustration_id)
                if illustration is not None:
                    approved_illustration_ids.append(approve_illustration(session, illustration).id)
            result["approved_illustration_ids"] = approved_illustration_ids

    assemble_result = handle_assemble_book(
        session,
        {
            "story_draft_id": approved_draft.id,
            "language": "en",
            "publish_immediately": bool(payload.get("publish_immediately", False)),
            "replace_existing": True,
        },
    )
    result.update(assemble_result)
    return result


def _dispatch_job(session: Session, job: WorkflowJob, payload: dict[str, Any]) -> dict[str, Any]:
    payload = {**payload, "_workflow_job_id": job.id}
    if job.job_type == "generate_story_ideas":
        return handle_generate_story_ideas(session, payload)
    if job.job_type == "generate_story_draft":
        return handle_generate_story_draft(session, payload)
    if job.job_type == "generate_illustration_plan":
        return handle_generate_illustration_plan(session, payload)
    if job.job_type == "generate_page_illustrations":
        return handle_generate_page_illustrations(session, payload)
    if job.job_type == "assemble_book":
        return handle_assemble_book(session, payload)
    if job.job_type == "generate_book_narration":
        return handle_generate_book_narration(session, payload)
    if job.job_type == "generate_daily_story_suggestion":
        return handle_generate_daily_story_suggestion(session, payload)
    if job.job_type == "full_story_pipeline":
        return handle_full_story_pipeline(session, payload)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported workflow job type")


def run_job(
    session: Session,
    *,
    job: WorkflowJob,
    actor_user_id: int | None = None,
    request_id: str | None = None,
) -> WorkflowJob:
    if job.status == "canceled":
        return job
    if job.status == "running":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow job is already running")
    if job.status == "succeeded":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow job has already succeeded")
    if job.attempt_count >= job.max_attempts and job.status == "failed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow job has exhausted its retry limit")

    job.status = "running"
    job.started_at = utc_now()
    job.completed_at = None
    job.error_message = None
    job.attempt_count += 1
    job.updated_at = utc_now()
    job = _persist_job(session, job)
    create_audit_log(
        session,
        action_type="workflow_job_run",
        entity_type="workflow_job",
        entity_id=str(job.id),
        summary=f"Started workflow job {job.id} ({job.job_type})",
        actor_user=_get_actor_user(session, actor_user_id or job.created_by_user_id),
        request_id=request_id,
        metadata={"job_type": job.job_type, "attempt_count": job.attempt_count},
    )

    try:
        payload = _deserialize_json(job.payload_json)
        result = _dispatch_job(session, job, payload)
        job.status = "succeeded"
        job.result_json = _serialize_json(result)
        job.error_message = None
        job.completed_at = utc_now()
        job.updated_at = utc_now()
        job = _persist_job(session, job)
        create_audit_log(
            session,
            action_type="workflow_job_succeeded",
            entity_type="workflow_job",
            entity_id=str(job.id),
            summary=f"Workflow job {job.id} succeeded",
            actor_user=_get_actor_user(session, actor_user_id or job.created_by_user_id),
            request_id=request_id,
            metadata={"job_type": job.job_type},
        )
        return job
    except Exception as exc:
        session.rollback()
        failed_job = get_workflow_job_or_404(session, job.id)
        failed_job.status = "failed"
        failed_job.error_message = str(exc)
        failed_job.completed_at = utc_now()
        failed_job.updated_at = utc_now()
        failed_job = _persist_job(session, failed_job)
        create_audit_log(
            session,
            action_type="workflow_job_failed",
            entity_type="workflow_job",
            entity_id=str(failed_job.id),
            summary=f"Workflow job {failed_job.id} failed",
            actor_user=_get_actor_user(session, actor_user_id or failed_job.created_by_user_id),
            request_id=request_id,
            metadata={"job_type": failed_job.job_type, "error_message": failed_job.error_message},
        )
        return failed_job


def run_job_by_id(job_id: int, actor_user_id: int | None = None, request_id: str | None = None) -> WorkflowJob:
    with Session(engine) as session:
        job = get_workflow_job_or_404(session, job_id)
        return run_job(session, job=job, actor_user_id=actor_user_id, request_id=request_id)


def run_queued_jobs(
    session: Session,
    *,
    limit: int,
    actor_user_id: int | None = None,
    request_id: str | None = None,
) -> list[WorkflowJob]:
    now = utc_now()
    queued_jobs = list(
        session.exec(
            select(WorkflowJob)
            .where(
                WorkflowJob.status == "queued",
                ((WorkflowJob.scheduled_for == None) | (WorkflowJob.scheduled_for <= now)),  # noqa: E711
            )
            .order_by(WorkflowJob.priority.asc(), WorkflowJob.created_at.asc())
            .limit(limit)
        ).all()
    )
    return [run_job_by_id(job.id, actor_user_id=actor_user_id, request_id=request_id) for job in queued_jobs]


def create_and_start_background_job(
    *,
    background_tasks: BackgroundTasks,
    session: Session,
    job_type: str,
    payload: dict[str, Any],
    created_by_user_id: int | None,
    request_id: str | None,
    priority: int = 5,
    max_attempts: int = 1,
    scheduled_for: datetime | None = None,
    parent_job_id: int | None = None,
) -> WorkflowJob:
    job = create_job(
        session,
        job_type=job_type,
        payload_json=_serialize_json(payload),
        created_by_user_id=created_by_user_id,
        priority=priority,
        scheduled_for=scheduled_for,
        max_attempts=max_attempts,
        parent_job_id=parent_job_id,
        request_id=request_id,
    )
    background_tasks.add_task(
        run_job_by_id,
        job.id,
        actor_user_id=created_by_user_id,
        request_id=request_id,
    )
    return job
