from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    AccountHealthSnapshot,
    AnalyticsEvent,
    ChildProfile,
    ReadingProgress,
    SupportTicket,
    User,
    UserLibraryItem,
)

HEALTH_BANDS = {"healthy", "watch", "at_risk", "churned"}
MEANINGFUL_ACTIVITY_EVENT_NAMES = {"app_opened", "library_viewed", "book_opened", "book_completed"}
OPEN_SUPPORT_STATUSES = {"open", "in_progress", "waiting_for_user"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass
class AccountHealthSignals:
    active_children_count: int
    stories_opened_30d: int
    stories_completed_30d: int
    saved_books_count: int
    support_tickets_open_count: int
    premium_status: str | None
    dormant_days: int | None
    reasoning_parts: list[str]


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def get_account_health_snapshot(session: Session, *, user_id: int) -> AccountHealthSnapshot | None:
    return session.exec(select(AccountHealthSnapshot).where(AccountHealthSnapshot.user_id == user_id)).first()


def get_account_health_snapshot_or_404(session: Session, *, user_id: int) -> AccountHealthSnapshot:
    snapshot = get_account_health_snapshot(session, user_id=user_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account health snapshot not found")
    return snapshot


def _collect_signals(session: Session, *, user: User) -> AccountHealthSignals:
    now = utc_now()
    since = now - timedelta(days=30)

    active_children_count = len(
        list(
            session.exec(
                select(ChildProfile).where(ChildProfile.user_id == user.id, ChildProfile.is_active.is_(True))
            ).all()
        )
    )

    reader_identifier = f"user:{user.id}"
    progresses = list(
        session.exec(
            select(ReadingProgress).where(ReadingProgress.reader_identifier == reader_identifier)
        ).all()
    )
    recent_progresses = [progress for progress in progresses if _normalize_datetime(progress.last_opened_at) and _normalize_datetime(progress.last_opened_at) >= since]
    stories_opened_30d = len(recent_progresses)
    stories_completed_30d = sum(
        1
        for progress in progresses
        if progress.completed and _normalize_datetime(progress.updated_at or progress.last_opened_at) and _normalize_datetime(progress.updated_at or progress.last_opened_at) >= since
    )

    saved_books_count = len(
        list(
            session.exec(
                select(UserLibraryItem).where(UserLibraryItem.user_id == user.id, UserLibraryItem.status == "saved")
            ).all()
        )
    )

    support_tickets_open_count = len(
        list(
            session.exec(
                select(SupportTicket).where(
                    SupportTicket.user_id == user.id,
                    SupportTicket.status.in_(tuple(OPEN_SUPPORT_STATUSES)),
                )
            ).all()
        )
    )

    premium_status = user.subscription_status if user.subscription_tier == "premium" else "none"
    if user.is_admin:
        premium_status = "active"

    recent_events = list(
        session.exec(
            select(AnalyticsEvent).where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_name.in_(tuple(MEANINGFUL_ACTIVITY_EVENT_NAMES)),
            )
        ).all()
    )
    candidate_activity_times = [
        _normalize_datetime(event.occurred_at) for event in recent_events
    ] + [
        _normalize_datetime(progress.last_opened_at) for progress in progresses
    ]
    candidate_activity_times = [value for value in candidate_activity_times if value is not None]
    last_activity_at = max(candidate_activity_times) if candidate_activity_times else _normalize_datetime(user.created_at)
    dormant_days = (now - last_activity_at).days if last_activity_at is not None else None

    reasoning_parts: list[str] = []
    if active_children_count:
        reasoning_parts.append(f"{active_children_count} active child profiles")
    else:
        reasoning_parts.append("no active child profiles")
    if stories_opened_30d:
        reasoning_parts.append(f"{stories_opened_30d} story opens in 30d")
    else:
        reasoning_parts.append("no story opens in 30d")
    if stories_completed_30d:
        reasoning_parts.append(f"{stories_completed_30d} story completions in 30d")
    if saved_books_count:
        reasoning_parts.append(f"{saved_books_count} saved books")
    if support_tickets_open_count:
        reasoning_parts.append(f"{support_tickets_open_count} open support tickets")
    if premium_status and premium_status != "none":
        reasoning_parts.append(f"premium status {premium_status}")
    if dormant_days is not None:
        reasoning_parts.append(f"{dormant_days} dormant days")

    return AccountHealthSignals(
        active_children_count=active_children_count,
        stories_opened_30d=stories_opened_30d,
        stories_completed_30d=stories_completed_30d,
        saved_books_count=saved_books_count,
        support_tickets_open_count=support_tickets_open_count,
        premium_status=premium_status,
        dormant_days=dormant_days,
        reasoning_parts=reasoning_parts,
    )


def _compute_health_score(*, signals: AccountHealthSignals) -> tuple[int, str]:
    score = 50
    score += min(signals.active_children_count * 10, 20)
    score += min(signals.stories_opened_30d * 3, 18)
    score += min(signals.stories_completed_30d * 5, 20)
    score += min(signals.saved_books_count * 2, 10)

    if signals.premium_status == "active":
        score += 15
    elif signals.premium_status == "trialing":
        score += 8
    elif signals.premium_status in {"past_due", "canceled", "expired"}:
        score -= 18

    if signals.support_tickets_open_count > 0:
        score -= min(signals.support_tickets_open_count * 8, 24)

    if signals.dormant_days is not None:
        if signals.dormant_days >= 60:
            score -= 35
        elif signals.dormant_days >= 30:
            score -= 25
        elif signals.dormant_days >= 14:
            score -= 15
        elif signals.dormant_days >= 7:
            score -= 8

    if signals.active_children_count == 0 and signals.stories_opened_30d == 0:
        score -= 15
    if signals.stories_opened_30d == 0 and signals.stories_completed_30d == 0:
        score -= 10

    bounded = max(0, min(100, score))
    if bounded >= 70:
        return bounded, "healthy"
    if bounded >= 45:
        return bounded, "watch"
    if bounded >= 20:
        return bounded, "at_risk"
    return bounded, "churned"


def rebuild_account_health_snapshot(session: Session, *, user: User) -> AccountHealthSnapshot:
    signals = _collect_signals(session, user=user)
    score, band = _compute_health_score(signals=signals)
    snapshot = get_account_health_snapshot(session, user_id=user.id)
    generated_at = utc_now()
    if snapshot is None:
        snapshot = AccountHealthSnapshot(user_id=user.id)
    snapshot.health_score = score
    snapshot.health_band = band
    snapshot.active_children_count = signals.active_children_count
    snapshot.stories_opened_30d = signals.stories_opened_30d
    snapshot.stories_completed_30d = signals.stories_completed_30d
    snapshot.saved_books_count = signals.saved_books_count
    snapshot.support_tickets_open_count = signals.support_tickets_open_count
    snapshot.premium_status = signals.premium_status
    snapshot.dormant_days = signals.dormant_days
    snapshot.snapshot_reasoning = "; ".join(signals.reasoning_parts)
    snapshot.generated_at = generated_at
    snapshot.updated_at = generated_at
    return _persist(session, snapshot)


def rebuild_all_account_health_snapshots(session: Session) -> list[AccountHealthSnapshot]:
    users = list(session.exec(select(User).order_by(User.created_at.desc())).all())
    return [rebuild_account_health_snapshot(session, user=user) for user in users]


def list_account_health_snapshots(
    session: Session,
    *,
    health_band: str | None = None,
    premium_status: str | None = None,
    limit: int = 100,
) -> list[AccountHealthSnapshot]:
    statement = select(AccountHealthSnapshot).order_by(AccountHealthSnapshot.health_score.asc(), AccountHealthSnapshot.generated_at.desc()).limit(limit)
    if health_band is not None:
        if health_band not in HEALTH_BANDS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid health band")
        statement = statement.where(AccountHealthSnapshot.health_band == health_band)
    if premium_status is not None:
        statement = statement.where(AccountHealthSnapshot.premium_status == premium_status)
    return list(session.exec(statement).all())


def build_snapshot_response(session: Session, *, snapshot: AccountHealthSnapshot) -> dict:
    user = session.get(User, snapshot.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "snapshot": snapshot,
        "user_email": user.email,
        "user_display_name": user.display_name,
    }


def build_summary_response(session: Session, *, snapshots: list[AccountHealthSnapshot]) -> dict:
    return {
        "items": [build_snapshot_response(session, snapshot=snapshot) for snapshot in snapshots],
        "total": len(snapshots),
    }
