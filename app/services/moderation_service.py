from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, ModerationCase, QualityCheck, StoryDraft, StoryPage, SupportTicket
from app.services.review_service import utc_now
from app.services.user_service import get_user_by_id

MODERATION_CASE_TYPES = {"content_concern", "quality_failure", "manual_escalation", "parental_report"}
MODERATION_CASE_STATUSES = {"open", "triaging", "resolved", "dismissed"}
MODERATION_SEVERITIES = {"low", "medium", "high", "critical"}
MODERATION_TARGET_TYPES = {"book", "story_draft", "story_page", "story_pages", "support_ticket", "quality_check", "unknown"}
MODERATION_SOURCE_TYPES = {"support_ticket", "quality_check", "manual", "parent_report", "system"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_case_type(case_type: str) -> str:
    if case_type not in MODERATION_CASE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid moderation case type")
    return case_type


def validate_case_status(status_value: str) -> str:
    if status_value not in MODERATION_CASE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid moderation case status")
    return status_value


def validate_case_severity(severity: str) -> str:
    if severity not in MODERATION_SEVERITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid moderation severity")
    return severity


def validate_target_type(target_type: str) -> str:
    if target_type not in MODERATION_TARGET_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid moderation target type")
    return target_type


def validate_source_type(source_type: str) -> str:
    if source_type not in MODERATION_SOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid moderation source type")
    return source_type


def _validate_assignee(session: Session, *, assigned_to_user_id: int | None) -> None:
    if assigned_to_user_id is None:
        return
    user = get_user_by_id(session, assigned_to_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found")
    if not user.is_admin and not user.is_editor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user must be editor or admin")


def get_moderation_case_or_404(session: Session, *, case_id: int) -> ModerationCase:
    moderation_case = session.get(ModerationCase, case_id)
    if moderation_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Moderation case not found")
    return moderation_case


def list_moderation_cases(
    session: Session,
    *,
    status_value: str | None,
    severity: str | None,
    case_type: str | None,
    assigned_to_user_id: int | None,
    limit: int,
) -> list[ModerationCase]:
    statement = select(ModerationCase).order_by(ModerationCase.updated_at.desc()).limit(limit)
    if status_value is not None:
        statement = statement.where(ModerationCase.status == validate_case_status(status_value))
    if severity is not None:
        statement = statement.where(ModerationCase.severity == validate_case_severity(severity))
    if case_type is not None:
        statement = statement.where(ModerationCase.case_type == validate_case_type(case_type))
    if assigned_to_user_id is not None:
        statement = statement.where(ModerationCase.assigned_to_user_id == assigned_to_user_id)
    return list(session.exec(statement).all())


def create_moderation_case(
    session: Session,
    *,
    case_type: str,
    target_type: str,
    target_id: int | None,
    source_type: str,
    source_id: int | None,
    severity: str,
    status_value: str,
    summary: str,
    notes: str | None,
    assigned_to_user_id: int | None,
) -> ModerationCase:
    validate_case_type(case_type)
    validate_target_type(target_type)
    validate_source_type(source_type)
    validate_case_severity(severity)
    validate_case_status(status_value)
    _validate_assignee(session, assigned_to_user_id=assigned_to_user_id)
    moderation_case = ModerationCase(
        case_type=case_type,
        target_type=target_type,
        target_id=target_id,
        source_type=source_type,
        source_id=source_id,
        severity=severity,
        status=status_value,
        summary=summary.strip(),
        notes=notes,
        assigned_to_user_id=assigned_to_user_id,
    )
    if moderation_case.status in {"resolved", "dismissed"}:
        moderation_case.resolved_at = utc_now()
    return _persist(session, moderation_case)


def get_open_case_for_source(
    session: Session,
    *,
    source_type: str,
    source_id: int | None,
) -> ModerationCase | None:
    if source_id is None:
        return None
    return session.exec(
        select(ModerationCase).where(
            ModerationCase.source_type == source_type,
            ModerationCase.source_id == source_id,
            ModerationCase.status.in_(["open", "triaging"]),
        )
    ).first()


def create_case_if_missing(
    session: Session,
    *,
    case_type: str,
    target_type: str,
    target_id: int | None,
    source_type: str,
    source_id: int | None,
    severity: str,
    summary: str,
    notes: str | None = None,
) -> ModerationCase:
    existing = get_open_case_for_source(session, source_type=source_type, source_id=source_id)
    if existing is not None:
        return existing
    return create_moderation_case(
        session,
        case_type=case_type,
        target_type=target_type,
        target_id=target_id,
        source_type=source_type,
        source_id=source_id,
        severity=severity,
        status_value="open",
        summary=summary,
        notes=notes,
        assigned_to_user_id=None,
    )


def get_open_case_for_target(
    session: Session,
    *,
    case_type: str,
    target_type: str,
    target_id: int | None,
) -> ModerationCase | None:
    if target_id is None:
        return None
    return session.exec(
        select(ModerationCase).where(
            ModerationCase.case_type == case_type,
            ModerationCase.target_type == target_type,
            ModerationCase.target_id == target_id,
            ModerationCase.status.in_(["open", "triaging"]),
        )
    ).first()


def update_moderation_case(
    session: Session,
    *,
    moderation_case: ModerationCase,
    severity: str | None = None,
    status_value: str | None = None,
    summary: str | None = None,
    notes: str | None = None,
    assigned_to_user_id: int | None = None,
    resolved_at=None,
    assigned_to_user_id_provided: bool = False,
    notes_provided: bool = False,
    resolved_at_provided: bool = False,
) -> ModerationCase:
    if severity is not None:
        moderation_case.severity = validate_case_severity(severity)
    if status_value is not None:
        moderation_case.status = validate_case_status(status_value)
        if moderation_case.status in {"resolved", "dismissed"}:
            moderation_case.resolved_at = resolved_at or utc_now()
        elif resolved_at is None:
            moderation_case.resolved_at = None
    if summary is not None:
        moderation_case.summary = summary.strip()
    if notes_provided:
        moderation_case.notes = notes
    if assigned_to_user_id_provided:
        _validate_assignee(session, assigned_to_user_id=assigned_to_user_id)
        moderation_case.assigned_to_user_id = assigned_to_user_id
    if resolved_at_provided:
        moderation_case.resolved_at = resolved_at
    moderation_case.updated_at = utc_now()
    return _persist(session, moderation_case)


def resolve_moderation_case(session: Session, *, moderation_case: ModerationCase) -> ModerationCase:
    moderation_case.status = "resolved"
    moderation_case.resolved_at = utc_now()
    moderation_case.updated_at = utc_now()
    return _persist(session, moderation_case)


def dismiss_moderation_case(session: Session, *, moderation_case: ModerationCase) -> ModerationCase:
    moderation_case.status = "dismissed"
    moderation_case.resolved_at = utc_now()
    moderation_case.updated_at = utc_now()
    return _persist(session, moderation_case)


def build_case_detail_response(session: Session, *, moderation_case: ModerationCase):
    from app.schemas.moderation_schema import ModerationCaseDetailResponse, ModerationCaseRead

    target_summary = None
    source_summary = None
    if moderation_case.target_type == "book" and moderation_case.target_id is not None:
        book = session.get(Book, moderation_case.target_id)
        target_summary = f"Book: {book.title}" if book is not None else f"Book #{moderation_case.target_id}"
    elif moderation_case.target_type == "story_draft" and moderation_case.target_id is not None:
        draft = session.get(StoryDraft, moderation_case.target_id)
        target_summary = f"Draft: {draft.title}" if draft is not None else f"Story draft #{moderation_case.target_id}"
    elif moderation_case.target_type in {"story_page", "story_pages"} and moderation_case.target_id is not None:
        page = session.get(StoryPage, moderation_case.target_id) if moderation_case.target_type == "story_page" else None
        target_summary = (
            f"Story page {page.page_number}" if page is not None else f"{moderation_case.target_type.replace('_', ' ')} #{moderation_case.target_id}"
        )
    elif moderation_case.target_type == "support_ticket" and moderation_case.target_id is not None:
        ticket = session.get(SupportTicket, moderation_case.target_id)
        target_summary = f"Support ticket: {ticket.subject}" if ticket is not None else f"Support ticket #{moderation_case.target_id}"
    elif moderation_case.target_type == "quality_check" and moderation_case.target_id is not None:
        check = session.get(QualityCheck, moderation_case.target_id)
        target_summary = f"Quality check: {check.check_type}" if check is not None else f"Quality check #{moderation_case.target_id}"

    if moderation_case.source_type == "support_ticket" and moderation_case.source_id is not None:
        ticket = session.get(SupportTicket, moderation_case.source_id)
        source_summary = f"Support ticket: {ticket.subject}" if ticket is not None else f"Support ticket #{moderation_case.source_id}"
    elif moderation_case.source_type == "quality_check" and moderation_case.source_id is not None:
        check = session.get(QualityCheck, moderation_case.source_id)
        source_summary = f"Quality check: {check.check_type}" if check is not None else f"Quality check #{moderation_case.source_id}"
    elif moderation_case.source_type == "manual":
        source_summary = "Manual escalation"
    elif moderation_case.source_type == "system":
        source_summary = "System escalation"
    elif moderation_case.source_type == "parent_report":
        source_summary = "Parent report"

    return ModerationCaseDetailResponse(
        case=ModerationCaseRead.model_validate(moderation_case),
        target_summary=target_summary,
        source_summary=source_summary,
    )


def escalate_support_ticket_if_needed(session: Session, *, ticket: SupportTicket) -> ModerationCase | None:
    if ticket.category != "content_concern":
        return None
    target_type = "book" if ticket.related_book_id is not None else "support_ticket"
    target_id = ticket.related_book_id if ticket.related_book_id is not None else ticket.id
    return create_case_if_missing(
        session,
        case_type="parental_report",
        target_type=target_type,
        target_id=target_id,
        source_type="support_ticket",
        source_id=ticket.id,
        severity="medium",
        summary=f"Parent content concern reported in support ticket {ticket.id}",
        notes=ticket.message,
    )


def _severity_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(value, 1)


def _severity_from_quality_check(check: QualityCheck) -> str:
    if check.status != "failed":
        return "medium"
    issues_json = check.issues_json or ""
    lowered = issues_json.lower()
    if '"severity": "high"' in lowered or "critical" in lowered:
        return "high"
    if check.check_type == "overall_quality":
        return "high"
    return "medium"


def escalate_failed_quality_checks(
    session: Session,
    *,
    checks: list[QualityCheck],
    target_type: str,
    target_id: int,
) -> ModerationCase | None:
    failed_checks = [check for check in checks if check.status == "failed"]
    if not failed_checks:
        return None
    existing = get_open_case_for_target(session, case_type="quality_failure", target_type=target_type, target_id=target_id)
    if existing is not None:
        return existing
    source_check = next((check for check in failed_checks if check.check_type == "overall_quality"), failed_checks[0])
    severity = max((_severity_from_quality_check(check) for check in failed_checks), key=_severity_rank)
    summary = f"Quality failure escalation for {target_type} {target_id}"
    notes = " | ".join(check.summary for check in failed_checks[:3])
    return create_case_if_missing(
        session,
        case_type="quality_failure",
        target_type=target_type,
        target_id=target_id,
        source_type="quality_check",
        source_id=source_check.id,
        severity=severity,
        summary=summary,
        notes=notes,
    )
