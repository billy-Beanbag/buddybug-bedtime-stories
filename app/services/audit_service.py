from __future__ import annotations

import json
import logging
from typing import Any

from sqlmodel import Session

from app.models import AuditLog, User

logger = logging.getLogger(__name__)


def _serialize_metadata(metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None
    try:
        return json.dumps(metadata, default=str, sort_keys=True)
    except Exception:
        return json.dumps({"serialization_error": True}, default=str)


def create_audit_log(
    session: Session,
    *,
    action_type: str,
    entity_type: str,
    entity_id: str | None,
    summary: str,
    actor_user: User | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog | None:
    """Persist an audit log record without breaking the primary workflow on failure."""
    try:
        audit_log = AuditLog(
            actor_user_id=actor_user.id if actor_user is not None else None,
            actor_email=actor_user.email if actor_user is not None else None,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            metadata_json=_serialize_metadata(metadata),
            request_id=request_id,
        )
        session.add(audit_log)
        session.commit()
        session.refresh(audit_log)
        return audit_log
    except Exception:
        session.rollback()
        logger.warning(
            "Failed to persist audit log",
            exc_info=True,
            extra={
                "action_type": action_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "request_id": request_id,
            },
        )
        return None
