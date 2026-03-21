from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import QualityCheck, User
from app.schemas.quality_schema import (
    DraftQualityRunRequest,
    QualityCheckBatchResponse,
    QualityCheckRead,
    QualitySummaryResponse,
    StoryPagesQualityRunRequest,
)
from app.services.audit_service import create_audit_log
from app.services.moderation_service import escalate_failed_quality_checks
from app.services.quality_service import (
    get_overall_quality_status,
    get_quality_checks_for_target,
    list_quality_checks,
    run_story_draft_quality_checks,
    run_story_pages_quality_checks,
    _validate_target_type,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/quality", tags=["quality"])
admin_router = APIRouter(prefix="/admin/quality", tags=["admin-quality"])


def _build_batch_response(target_type: str, target_id: int, checks: list[QualityCheck]) -> QualityCheckBatchResponse:
    return QualityCheckBatchResponse(
        target_type=target_type,
        target_id=target_id,
        checks=[QualityCheckRead.model_validate(check) for check in checks],
    )


def _create_quality_run_audit(
    *,
    session: Session,
    request: Request,
    current_user: User,
    target_type: str,
    target_id: int,
    checks: list[QualityCheck],
) -> None:
    overall_status = next((check.status for check in checks if check.check_type == "overall_quality"), "passed")
    create_audit_log(
        session,
        action_type="quality_checks_run",
        entity_type=target_type,
        entity_id=str(target_id),
        summary=f"Ran quality checks for {target_type} {target_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"overall_status": overall_status, "check_count": len(checks)},
    )
    if overall_status == "warning":
        create_audit_log(
            session,
            action_type="quality_checks_warning_detected",
            entity_type=target_type,
            entity_id=str(target_id),
            summary=f"Quality warnings detected for {target_type} {target_id}",
            actor_user=current_user,
            request_id=get_request_id_from_request(request),
            metadata={"overall_status": overall_status},
        )
    if overall_status == "failed":
        create_audit_log(
            session,
            action_type="quality_checks_failed_detected",
            entity_type=target_type,
            entity_id=str(target_id),
            summary=f"Quality failures detected for {target_type} {target_id}",
            actor_user=current_user,
            request_id=get_request_id_from_request(request),
            metadata={"overall_status": overall_status},
        )


@router.post("/story-drafts/run", response_model=QualityCheckBatchResponse, summary="Run quality checks for a story draft")
def run_story_draft_checks(
    payload: DraftQualityRunRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> QualityCheckBatchResponse:
    checks = run_story_draft_quality_checks(session, story_draft_id=payload.story_draft_id)
    _create_quality_run_audit(
        session=session,
        request=request,
        current_user=current_user,
        target_type="story_draft",
        target_id=payload.story_draft_id,
        checks=checks,
    )
    escalate_failed_quality_checks(session, checks=checks, target_type="story_draft", target_id=payload.story_draft_id)
    return _build_batch_response("story_draft", payload.story_draft_id, checks)


@router.post("/story-pages/run", response_model=QualityCheckBatchResponse, summary="Run quality checks for story pages")
def run_story_pages_checks(
    payload: StoryPagesQualityRunRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> QualityCheckBatchResponse:
    checks = run_story_pages_quality_checks(session, story_draft_id=payload.story_draft_id)
    _create_quality_run_audit(
        session=session,
        request=request,
        current_user=current_user,
        target_type="story_pages",
        target_id=payload.story_draft_id,
        checks=checks,
    )
    escalate_failed_quality_checks(session, checks=checks, target_type="story_pages", target_id=payload.story_draft_id)
    return _build_batch_response("story_pages", payload.story_draft_id, checks)


@router.get("/checks", response_model=list[QualityCheckRead], summary="List quality checks")
def get_quality_checks(
    target_type: str | None = Query(default=None),
    target_id: int | None = Query(default=None),
    check_type: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=250),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_active_user),
) -> list[QualityCheck]:
    return list_quality_checks(
        session,
        target_type=target_type,
        target_id=target_id,
        check_type=check_type,
        status_value=status_value,
        limit=limit,
    )


@router.get("/{target_type}/{target_id}", response_model=QualitySummaryResponse, summary="Get quality summary for a target")
def get_quality_summary(
    target_type: str,
    target_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_active_user),
) -> QualitySummaryResponse:
    checks = get_quality_checks_for_target(session, target_type=target_type, target_id=target_id)
    return QualitySummaryResponse(
        target_type=target_type,
        target_id=target_id,
        overall_status=get_overall_quality_status(session, target_type=target_type, target_id=target_id),
        checks=[QualityCheckRead.model_validate(check) for check in checks],
    )


@admin_router.get("/warnings", response_model=list[QualityCheckRead], summary="List warning and failed quality checks")
def list_quality_warnings(
    target_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=250),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[QualityCheck]:
    statement = (
        select(QualityCheck)
        .where(QualityCheck.status.in_(["warning", "failed"]))
        .order_by(QualityCheck.created_at.desc())
        .limit(limit)
    )
    if target_type is not None:
        _validate_target_type(target_type)
        statement = statement.where(QualityCheck.target_type == target_type)
    return list(session.exec(statement).all())
