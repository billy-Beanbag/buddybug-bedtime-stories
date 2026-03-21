from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import AuditLog, User
from app.schemas.audit_schema import AuditLogRead
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogRead], summary="List audit log records")
def list_audit_logs(
    action_type: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if action_type:
        statement = statement.where(AuditLog.action_type == action_type)
    if entity_type:
        statement = statement.where(AuditLog.entity_type == entity_type)
    if actor_user_id is not None:
        statement = statement.where(AuditLog.actor_user_id == actor_user_id)
    return list(session.exec(statement).all())


@router.get("/{audit_id}", response_model=AuditLogRead, summary="Get one audit log record")
def get_audit_log(
    audit_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AuditLog:
    audit_log = session.get(AuditLog, audit_id)
    if audit_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return audit_log
