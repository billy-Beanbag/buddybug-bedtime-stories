from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.account_health_schema import AccountHealthSnapshotResponse, AccountHealthSummaryResponse
from app.services.account_health_service import (
    build_snapshot_response,
    build_summary_response,
    get_account_health_snapshot_or_404,
    list_account_health_snapshots,
    rebuild_account_health_snapshot,
    rebuild_all_account_health_snapshots,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin/account-health", tags=["admin-account-health"])


@router.get("", response_model=AccountHealthSummaryResponse, summary="List account health snapshots")
def list_account_health(
    health_band: str | None = Query(default=None),
    premium_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AccountHealthSummaryResponse:
    snapshots = list_account_health_snapshots(
        session,
        health_band=health_band,
        premium_status=premium_status,
        limit=limit,
    )
    return AccountHealthSummaryResponse(**build_summary_response(session, snapshots=snapshots))


@router.get("/{user_id}", response_model=AccountHealthSnapshotResponse, summary="Get one account health snapshot")
def get_account_health(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AccountHealthSnapshotResponse:
    snapshot = get_account_health_snapshot_or_404(session, user_id=user_id)
    return AccountHealthSnapshotResponse(**build_snapshot_response(session, snapshot=snapshot))


@router.post("/{user_id}/rebuild", response_model=AccountHealthSnapshotResponse, summary="Rebuild one account health snapshot")
def rebuild_one_account_health(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AccountHealthSnapshotResponse:
    user = session.get(User, user_id)
    if user is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    snapshot = rebuild_account_health_snapshot(session, user=user)
    return AccountHealthSnapshotResponse(**build_snapshot_response(session, snapshot=snapshot))


@router.post("/rebuild-all", response_model=AccountHealthSummaryResponse, summary="Rebuild all account health snapshots")
def rebuild_all_account_health(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AccountHealthSummaryResponse:
    snapshots = rebuild_all_account_health_snapshots(session)
    return AccountHealthSummaryResponse(**build_summary_response(session, snapshots=snapshots))
