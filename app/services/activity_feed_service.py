from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import AuditLog, ModerationCase, SupportTicket, SupportTicketNote, User, WorkflowJob
from app.schemas.activity_feed_schema import ActivityFeedItem, ActivityFeedResponse


def _serialize_metadata(metadata: dict[str, object] | None) -> str | None:
    if not metadata:
        return None
    return json.dumps(metadata, default=str, sort_keys=True)


def _sort_and_limit(items: list[ActivityFeedItem], limit: int) -> ActivityFeedResponse:
    sorted_items = sorted(items, key=lambda item: item.timestamp, reverse=True)
    return ActivityFeedResponse(items=sorted_items[:limit])


def _audit_items_for_entity(session: Session, *, entity_type: str, entity_id: int) -> list[ActivityFeedItem]:
    audit_logs = list(
        session.exec(
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == str(entity_id))
            .order_by(AuditLog.created_at.desc())
        ).all()
    )
    return [
        ActivityFeedItem(
            timestamp=audit.created_at,
            event_type=audit.action_type,
            entity_type=audit.entity_type,
            entity_id=audit.entity_id,
            summary=audit.summary,
            actor_user_id=audit.actor_user_id,
            actor_email=audit.actor_email,
            source_table="audit_log",
            metadata_json=audit.metadata_json,
        )
        for audit in audit_logs
    ]


def _audit_items_for_user(session: Session, *, user_id: int) -> list[ActivityFeedItem]:
    audit_logs = list(
        session.exec(
            select(AuditLog)
            .where((AuditLog.actor_user_id == user_id) | ((AuditLog.entity_type == "user") & (AuditLog.entity_id == str(user_id))))
            .order_by(AuditLog.created_at.desc())
        ).all()
    )
    return [
        ActivityFeedItem(
            timestamp=audit.created_at,
            event_type=audit.action_type,
            entity_type=audit.entity_type,
            entity_id=audit.entity_id,
            summary=audit.summary,
            actor_user_id=audit.actor_user_id,
            actor_email=audit.actor_email,
            source_table="audit_log",
            metadata_json=audit.metadata_json,
        )
        for audit in audit_logs
    ]


def _support_note_items(session: Session, *, ticket_id: int) -> list[ActivityFeedItem]:
    notes = list(
        session.exec(
            select(SupportTicketNote)
            .where(SupportTicketNote.ticket_id == ticket_id)
            .order_by(SupportTicketNote.created_at.desc())
        ).all()
    )
    authors = {
        user.id: user
        for user in session.exec(
            select(User).where(User.id.in_([note.author_user_id for note in notes if note.author_user_id is not None]))
        ).all()
    } if notes else {}
    items: list[ActivityFeedItem] = []
    for note in notes:
        author = authors.get(note.author_user_id) if note.author_user_id is not None else None
        items.append(
            ActivityFeedItem(
                timestamp=note.created_at,
                event_type="support_ticket_note_added",
                entity_type="support_ticket",
                entity_id=str(ticket_id),
                summary=f"Added {note.note_type} note on support ticket {ticket_id}",
                actor_user_id=note.author_user_id,
                actor_email=author.email if author is not None else None,
                source_table="support_ticket_note",
                metadata_json=_serialize_metadata({"note_id": note.id, "note_type": note.note_type, "is_internal": note.is_internal}),
            )
        )
    return items


def _moderation_items_for_entity(session: Session, *, entity_type: str, entity_id: int) -> list[ActivityFeedItem]:
    moderation_cases = list(
        session.exec(
            select(ModerationCase)
            .where(
                ((ModerationCase.target_type == entity_type) & (ModerationCase.target_id == entity_id))
                | ((ModerationCase.source_type == entity_type) & (ModerationCase.source_id == entity_id))
            )
            .order_by(ModerationCase.updated_at.desc())
        ).all()
    )
    items: list[ActivityFeedItem] = []
    for moderation_case in moderation_cases:
        relation = (
            "target"
            if moderation_case.target_type == entity_type and moderation_case.target_id == entity_id
            else "source"
        )
        items.append(
            ActivityFeedItem(
                timestamp=moderation_case.updated_at,
                event_type=f"moderation_case_{moderation_case.status}",
                entity_type=entity_type,
                entity_id=str(entity_id),
                summary=f"Moderation case {moderation_case.id}: {moderation_case.summary}",
                actor_user_id=None,
                actor_email=None,
                source_table="moderation_case",
                metadata_json=_serialize_metadata(
                    {
                        "moderation_case_id": moderation_case.id,
                        "case_type": moderation_case.case_type,
                        "severity": moderation_case.severity,
                        "status": moderation_case.status,
                        "relation": relation,
                    }
                ),
            )
        )
    return items


def _support_ticket_items_for_user(session: Session, *, user_id: int) -> list[ActivityFeedItem]:
    tickets = list(
        session.exec(
            select(SupportTicket).where(SupportTicket.user_id == user_id).order_by(SupportTicket.updated_at.desc())
        ).all()
    )
    items: list[ActivityFeedItem] = []
    for ticket in tickets:
        items.append(
            ActivityFeedItem(
                timestamp=ticket.created_at,
                event_type="support_ticket_created",
                entity_type="support_ticket",
                entity_id=str(ticket.id),
                summary=f"Created support ticket '{ticket.subject}'",
                actor_user_id=ticket.user_id,
                actor_email=ticket.email,
                source_table="support_ticket",
                metadata_json=_serialize_metadata(
                    {
                        "ticket_id": ticket.id,
                        "category": ticket.category,
                        "status": ticket.status,
                        "priority": ticket.priority,
                    }
                ),
            )
        )
    return items


def _workflow_items_for_user(session: Session, *, user_id: int) -> list[ActivityFeedItem]:
    workflow_jobs = list(
        session.exec(
            select(WorkflowJob).where(WorkflowJob.created_by_user_id == user_id).order_by(WorkflowJob.updated_at.desc())
        ).all()
    )
    return [
        ActivityFeedItem(
            timestamp=job.updated_at,
            event_type=f"workflow_job_{job.status}",
            entity_type="workflow_job",
            entity_id=str(job.id),
            summary=f"Workflow job {job.id} for {job.job_type} is {job.status}",
            actor_user_id=job.created_by_user_id,
            actor_email=None,
            source_table="workflow_job",
            metadata_json=_serialize_metadata(
                {
                    "job_type": job.job_type,
                    "status": job.status,
                    "attempt_count": job.attempt_count,
                    "scheduled_for": job.scheduled_for,
                }
            ),
        )
        for job in workflow_jobs
    ]


def get_entity_activity_feed(session: Session, *, entity_type: str, entity_id: int, limit: int = 100) -> ActivityFeedResponse:
    items = _audit_items_for_entity(session, entity_type=entity_type, entity_id=entity_id)
    if entity_type == "support_ticket":
        items.extend(_support_note_items(session, ticket_id=entity_id))
    items.extend(_moderation_items_for_entity(session, entity_type=entity_type, entity_id=entity_id))
    return _sort_and_limit(items, limit)


def get_user_activity_feed(session: Session, *, user_id: int, limit: int = 100) -> ActivityFeedResponse:
    if session.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    items = _audit_items_for_user(session, user_id=user_id)
    items.extend(_support_ticket_items_for_user(session, user_id=user_id))
    items.extend(_workflow_items_for_user(session, user_id=user_id))
    return _sort_and_limit(items, limit)
