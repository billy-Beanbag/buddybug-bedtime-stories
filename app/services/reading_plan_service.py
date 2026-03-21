from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, ChildProfile, ReadingPlan, ReadingPlanSession, StoryDraft, User
from app.schemas.discovery_schema import DiscoverySearchResult
from app.services.child_comfort_service import ChildComfortSignals, get_child_comfort_signals
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.content_lane_service import validate_content_lane_key
from app.services.discovery_service import build_book_discovery_metadata, get_book_discovery_metadata
from app.services.i18n_service import get_book_translation, normalize_language, validate_language_code
from app.services.parental_controls_service import filter_books_by_parental_controls, resolve_parental_controls
from app.services.review_service import utc_now

READING_PLAN_STATUSES = {"active", "paused", "archived"}
READING_PLAN_TYPES = {"bedtime", "narrated", "language_practice", "family_reading", "custom"}
SUPPORTED_AGE_BANDS = {"3-7", "8-12"}
WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
UNSET = object()


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _validate_status(status_value: str) -> str:
    if status_value not in READING_PLAN_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported reading plan status")
    return status_value


def _validate_plan_type(plan_type: str) -> str:
    if plan_type not in READING_PLAN_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported reading plan type")
    return plan_type


def _validate_age_band(age_band: str | None) -> str | None:
    if age_band is None:
        return None
    if age_band not in SUPPORTED_AGE_BANDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported reading plan age band")
    return age_band


def _parse_target_days_csv(target_days_csv: str | None) -> list[str]:
    if target_days_csv is None or target_days_csv.strip() == "":
        return []
    days: list[str] = []
    for raw in target_days_csv.split(","):
        day = raw.strip().lower()
        if not day:
            continue
        if day not in WEEKDAY_KEYS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported reading plan weekday value")
        if day not in days:
            days.append(day)
    return days


def _serialize_target_days(days: list[str]) -> str | None:
    return ",".join(days) if days else None


def _resolve_plan_defaults(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
    preferred_age_band: str | None,
    preferred_language: str | None,
    preferred_content_lane_key: str | None,
) -> tuple[ChildProfile | None, str | None, str | None, str | None]:
    child_profile = validate_child_profile_ownership(session, user_id=user.id, child_profile_id=child_profile_id)
    comfort_signals = (
        get_child_comfort_signals(session, child_profile_id=child_profile.id) if child_profile is not None else None
    )
    resolved_age_band = _validate_age_band(preferred_age_band or (child_profile.age_band if child_profile is not None else None))
    resolved_language = (
        preferred_language
        or (comfort_signals.preferred_language if comfort_signals is not None else None)
        or (child_profile.language if child_profile is not None else user.language or "en")
    )
    normalized_language = validate_language_code(resolved_language) if resolved_language else None
    resolved_lane_key = preferred_content_lane_key or (child_profile.content_lane_key if child_profile is not None else None)
    if resolved_lane_key is not None:
        resolved_lane_key = validate_content_lane_key(
            session,
            age_band=resolved_age_band,
            content_lane_key=resolved_lane_key,
        ).key
    return child_profile, resolved_age_band, normalized_language, resolved_lane_key


def validate_plan_access(session: Session, *, user_id: int, plan_id: int) -> ReadingPlan:
    plan = session.get(ReadingPlan, plan_id)
    if plan is None or plan.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading plan not found")
    return plan


def create_reading_plan(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
    title: str,
    description: str | None,
    status: str,
    plan_type: str,
    preferred_age_band: str | None,
    preferred_language: str | None,
    preferred_content_lane_key: str | None,
    prefer_narration: bool,
    sessions_per_week: int,
    target_days_csv: str | None,
    bedtime_mode_preferred: bool,
) -> ReadingPlan:
    child_profile, resolved_age_band, resolved_language, resolved_lane_key = _resolve_plan_defaults(
        session,
        user=user,
        child_profile_id=child_profile_id,
        preferred_age_band=preferred_age_band,
        preferred_language=preferred_language,
        preferred_content_lane_key=preferred_content_lane_key,
    )
    plan = ReadingPlan(
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        title=title.strip(),
        description=description.strip() if description else None,
        status=_validate_status(status),
        plan_type=_validate_plan_type(plan_type),
        preferred_age_band=resolved_age_band,
        preferred_language=resolved_language,
        preferred_content_lane_key=resolved_lane_key,
        prefer_narration=prefer_narration,
        sessions_per_week=max(1, min(7, sessions_per_week)),
        target_days_csv=_serialize_target_days(_parse_target_days_csv(target_days_csv)),
        bedtime_mode_preferred=bedtime_mode_preferred,
    )
    return _persist(session, plan)


def update_reading_plan(
    session: Session,
    *,
    plan: ReadingPlan,
    user: User,
    changes: dict[str, object],
) -> ReadingPlan:
    child_profile_id = changes.get("child_profile_id", UNSET)
    title = changes.get("title", UNSET)
    description = changes.get("description", UNSET)
    status = changes.get("status", UNSET)
    plan_type = changes.get("plan_type", UNSET)
    preferred_age_band = changes.get("preferred_age_band", UNSET)
    preferred_language = changes.get("preferred_language", UNSET)
    preferred_content_lane_key = changes.get("preferred_content_lane_key", UNSET)
    prefer_narration = changes.get("prefer_narration", UNSET)
    sessions_per_week = changes.get("sessions_per_week", UNSET)
    target_days_csv = changes.get("target_days_csv", UNSET)
    bedtime_mode_preferred = changes.get("bedtime_mode_preferred", UNSET)

    resolved_child_profile_id = plan.child_profile_id if child_profile_id is UNSET else child_profile_id
    child_profile, resolved_age_band, resolved_language, resolved_lane_key = _resolve_plan_defaults(
        session,
        user=user,
        child_profile_id=resolved_child_profile_id,
        preferred_age_band=plan.preferred_age_band if preferred_age_band is UNSET else preferred_age_band,
        preferred_language=plan.preferred_language if preferred_language is UNSET else preferred_language,
        preferred_content_lane_key=(
            plan.preferred_content_lane_key if preferred_content_lane_key is UNSET else preferred_content_lane_key
        ),
    )
    if title is not UNSET:
        plan.title = str(title).strip()
    if description is not UNSET:
        plan.description = str(description).strip() if description else None
    if status is not UNSET:
        plan.status = _validate_status(status)
    if plan_type is not UNSET:
        plan.plan_type = _validate_plan_type(plan_type)
    plan.child_profile_id = child_profile.id if child_profile is not None else None
    plan.preferred_age_band = resolved_age_band
    plan.preferred_language = resolved_language
    plan.preferred_content_lane_key = resolved_lane_key
    if prefer_narration is not UNSET:
        plan.prefer_narration = bool(prefer_narration)
    if sessions_per_week is not UNSET:
        plan.sessions_per_week = max(1, min(7, sessions_per_week))
    if target_days_csv is not UNSET:
        plan.target_days_csv = _serialize_target_days(_parse_target_days_csv(target_days_csv))
    if bedtime_mode_preferred is not UNSET:
        plan.bedtime_mode_preferred = bool(bedtime_mode_preferred)
    plan.updated_at = utc_now()
    return _persist(session, plan)


def list_reading_plans_for_user(
    session: Session,
    *,
    user_id: int,
    status_value: str | None = None,
    child_profile_id: int | None = None,
) -> list[ReadingPlan]:
    statement = select(ReadingPlan).where(ReadingPlan.user_id == user_id)
    if status_value is not None:
        statement = statement.where(ReadingPlan.status == _validate_status(status_value))
    if child_profile_id is not None:
        statement = statement.where(ReadingPlan.child_profile_id == child_profile_id)
    return list(session.exec(statement.order_by(ReadingPlan.updated_at.desc(), ReadingPlan.created_at.desc())).all())


def _distributed_offsets(session_count: int) -> list[int]:
    resolved_count = max(1, min(7, session_count))
    if resolved_count == 1:
        return [0]
    offsets = sorted({round(index * 6 / (resolved_count - 1)) for index in range(resolved_count)})
    for offset in range(7):
        if len(offsets) >= resolved_count:
            break
        if offset not in offsets:
            offsets.append(offset)
    return sorted(offsets[:resolved_count])


def _target_dates_for_plan(*, plan: ReadingPlan, start_date: date, days_ahead: int) -> list[date]:
    target_days = set(_parse_target_days_csv(plan.target_days_csv))
    all_dates = [start_date + timedelta(days=offset) for offset in range(days_ahead)]
    if target_days:
        return [item for item in all_dates if WEEKDAY_KEYS[item.weekday()] in target_days]
    offsets = _distributed_offsets(plan.sessions_per_week)
    return [start_date + timedelta(days=offset) for offset in offsets]


def _build_discovery_result(
    session: Session,
    *,
    book: Book,
    preferred_language: str | None,
    score: float,
    reasons: list[str],
) -> DiscoverySearchResult:
    localized_title = book.title
    if preferred_language:
        translation = get_book_translation(session, book_id=book.id, language=preferred_language)
        if translation is not None and translation.title:
            localized_title = translation.title
    return DiscoverySearchResult(
        book_id=book.id,
        title=localized_title,
        cover_image_url=book.cover_image_url,
        age_band=book.age_band,
        language=book.language,
        content_lane_key=book.content_lane_key,
        published=book.published,
        publication_status=book.publication_status,
        score=score,
        reasons=reasons,
    )


def _candidate_books_for_plan(session: Session, *, user: User, plan: ReadingPlan) -> list[Book]:
    books = list(
        session.exec(
            select(Book).where(Book.published.is_(True), Book.publication_status == "published").order_by(Book.title.asc())
        ).all()
    )
    if plan.preferred_age_band:
        books = [book for book in books if book.age_band == plan.preferred_age_band]
    if plan.preferred_language:
        normalized_language = normalize_language(plan.preferred_language)
        books = [book for book in books if normalize_language(book.language) == normalized_language]
    if plan.preferred_content_lane_key:
        books = [book for book in books if book.content_lane_key == plan.preferred_content_lane_key]
    controls = resolve_parental_controls(session, user=user, child_profile_id=plan.child_profile_id)
    return filter_books_by_parental_controls(books, controls=controls)


def _draft_minutes_by_book(session: Session, *, books: list[Book]) -> dict[int, int | None]:
    draft_ids = [book.story_draft_id for book in books if book.story_draft_id is not None]
    if not draft_ids:
        return {}
    draft_map = {
        draft.id: draft.read_time_minutes
        for draft in session.exec(select(StoryDraft).where(StoryDraft.id.in_(draft_ids))).all()
    }
    return {book.id: draft_map.get(book.story_draft_id) for book in books}


def _comfort_plan_score(book: Book, *, comfort_signals: ChildComfortSignals | None, read_time_minutes: int | None) -> tuple[float, str | None]:
    if comfort_signals is None:
        return 0.0, None
    score = 0.0
    reason: str | None = None
    if comfort_signals.prefer_narration and book.audio_available:
        score += 10
        reason = "Aligned with narration comfort"
    if comfort_signals.preferred_language and normalize_language(book.language) == normalize_language(comfort_signals.preferred_language):
        score += 8
        reason = reason or "Matches the child's comfort language"
    if comfort_signals.extra_calm_mode and book.content_lane_key == "bedtime_3_7":
        score += 8
        reason = reason or "Leans extra calm"
    if comfort_signals.prefer_shorter_stories and read_time_minutes is not None and read_time_minutes <= 5:
        score += 7
        reason = reason or "A shorter, easier session fit"
    if "fast-paced" in comfort_signals.avoid_tags and "adventure" in (book.content_lane_key or "").lower():
        score -= 8
    if "loud" in comfort_signals.avoid_tags and "adventure" in (book.content_lane_key or "").lower():
        score -= 4
    return score, reason


def _split_metadata_tags(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _plan_mode_score(session: Session, *, book: Book, bedtime_mode_preferred: bool) -> tuple[float, str | None]:
    metadata = get_book_discovery_metadata(session, book_id=book.id) or build_book_discovery_metadata(session, book_id=book.id)
    tone_tags = _split_metadata_tags(metadata.tone_tags)
    style_tags = _split_metadata_tags(metadata.style_tags)
    if bedtime_mode_preferred and (tone_tags.intersection({"calm", "gentle", "bedtime"}) or style_tags.intersection({"calm", "bedtime"})):
        return 8.0, "Extra calm bedtime tone"
    if not bedtime_mode_preferred and (tone_tags.intersection({"playful", "cheeky"}) or style_tags.intersection({"playful", "cheeky"})):
        return 4.0, "Playful daytime tone"
    return 0.0, None


def suggest_books_for_plan(
    session: Session,
    *,
    user: User,
    plan: ReadingPlan,
    limit: int = 6,
) -> list[DiscoverySearchResult]:
    candidates = _candidate_books_for_plan(session, user=user, plan=plan)
    if not candidates:
        return []
    comfort_signals = (
        get_child_comfort_signals(session, child_profile_id=plan.child_profile_id) if plan.child_profile_id is not None else None
    )
    draft_minutes_map = _draft_minutes_by_book(session, books=candidates)

    def score_book(book: Book) -> tuple[float, str]:
        score = 0.0
        reasons: list[str] = []
        if plan.preferred_content_lane_key and book.content_lane_key == plan.preferred_content_lane_key:
            score += 40
            reasons.append("Matches the plan lane")
        if plan.preferred_age_band and book.age_band == plan.preferred_age_band:
            score += 30
            reasons.append("Fits the age band")
        if plan.preferred_language and normalize_language(book.language) == normalize_language(plan.preferred_language):
            score += 25
            reasons.append("Matches the reading language")
        if plan.prefer_narration and book.audio_available:
            score += 20
            reasons.append("Ready for narration")
        if not plan.prefer_narration and not book.audio_available:
            score += 5
            reasons.append("Simple read-together story")
        if plan.bedtime_mode_preferred and book.content_lane_key == "bedtime_3_7":
            score += 15
            reasons.append("A calm bedtime fit")
        if plan.plan_type == "family_reading":
            score += 5
            reasons.append("A flexible family read")
        mode_score, mode_reason = _plan_mode_score(
            session,
            book=book,
            bedtime_mode_preferred=plan.bedtime_mode_preferred,
        )
        score += mode_score
        if mode_reason is not None:
            reasons.append(mode_reason)
        comfort_score, comfort_reason = _comfort_plan_score(
            book,
            comfort_signals=comfort_signals,
            read_time_minutes=draft_minutes_map.get(book.id),
        )
        score += comfort_score
        if comfort_reason is not None:
            reasons.append(comfort_reason)
        if not reasons:
            reasons.append("A gentle match for this plan")
        return score, reasons[0]

    scored = []
    for book in candidates:
        score, primary_reason = score_book(book)
        scored.append(
            (
                -score,
                book.title.lower(),
                _build_discovery_result(
                    session,
                    book=book,
                    preferred_language=plan.preferred_language,
                    score=score,
                    reasons=[primary_reason],
                ),
            )
        )
    scored.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in scored[:limit]]


def generate_upcoming_sessions(
    session: Session,
    *,
    user: User,
    plan: ReadingPlan,
    days_ahead: int = 7,
) -> list[ReadingPlanSession]:
    start_date = utc_now().date()
    existing = list(
        session.exec(
            select(ReadingPlanSession).where(
                ReadingPlanSession.reading_plan_id == plan.id,
                ReadingPlanSession.scheduled_date >= start_date,
                ReadingPlanSession.scheduled_date < start_date + timedelta(days=days_ahead),
            )
        ).all()
    )
    if plan.status != "active":
        return sorted(existing, key=lambda item: item.scheduled_date)

    existing_by_date = {item.scheduled_date: item for item in existing}
    target_dates = _target_dates_for_plan(plan=plan, start_date=start_date, days_ahead=days_ahead)
    for scheduled_date in target_dates:
        if scheduled_date in existing_by_date:
            continue
        session_row = ReadingPlanSession(reading_plan_id=plan.id, scheduled_date=scheduled_date)
        session.add(session_row)
        session.commit()
        session.refresh(session_row)
        existing_by_date[scheduled_date] = session_row

    suggestions = suggest_books_for_plan(session, user=user, plan=plan, limit=max(len(target_dates), 6))
    suggested_ids = [item.book_id for item in suggestions]
    ordered_sessions = sorted(existing_by_date.values(), key=lambda item: item.scheduled_date)
    for index, item in enumerate(ordered_sessions):
        if item.suggested_book_id is not None or not suggested_ids:
            continue
        item.suggested_book_id = suggested_ids[index % len(suggested_ids)]
        item.updated_at = utc_now()
        session.add(item)
    session.commit()
    return ordered_sessions


def get_reading_plan_detail(
    session: Session,
    *,
    user: User,
    plan_id: int,
) -> tuple[ReadingPlan, list[ReadingPlanSession]]:
    plan = validate_plan_access(session, user_id=user.id, plan_id=plan_id)
    sessions = generate_upcoming_sessions(session, user=user, plan=plan)
    return plan, sessions


def mark_plan_session_completed(
    session: Session,
    *,
    user: User,
    plan_id: int,
    session_id: int,
) -> ReadingPlanSession:
    plan = validate_plan_access(session, user_id=user.id, plan_id=plan_id)
    session_row = session.get(ReadingPlanSession, session_id)
    if session_row is None or session_row.reading_plan_id != plan.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading plan session not found")
    if not session_row.completed:
        session_row.completed = True
        session_row.completed_at = utc_now()
        session_row.updated_at = utc_now()
    return _persist(session, session_row)


def archive_reading_plan(session: Session, *, user: User, plan_id: int) -> ReadingPlan:
    plan = validate_plan_access(session, user_id=user.id, plan_id=plan_id)
    plan.status = "archived"
    plan.updated_at = utc_now()
    return _persist(session, plan)


def list_active_reading_plans_for_context(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
) -> list[ReadingPlan]:
    statement = select(ReadingPlan).where(ReadingPlan.user_id == user_id, ReadingPlan.status == "active")
    if child_profile_id is not None:
        items = list(
            session.exec(
                statement.where(
                    (ReadingPlan.child_profile_id == child_profile_id) | (ReadingPlan.child_profile_id == None)  # noqa: E711
                )
            ).all()
        )
        items.sort(key=lambda item: (item.child_profile_id != child_profile_id, item.created_at))
        return items
    return list(session.exec(statement.where(ReadingPlan.child_profile_id == None).order_by(ReadingPlan.created_at.asc())).all())  # noqa: E711


def get_plan_story_candidate(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
    target_date: date,
) -> tuple[Book, str] | None:
    plans = list_active_reading_plans_for_context(session, user_id=user.id, child_profile_id=child_profile_id)
    for plan in plans:
        sessions = generate_upcoming_sessions(session, user=user, plan=plan)
        target_session = next((item for item in sessions if item.scheduled_date == target_date), None)
        if target_session is None and sessions:
            target_session = sessions[0]
        if target_session is not None and target_session.suggested_book_id is not None:
            book = session.get(Book, target_session.suggested_book_id)
            if book is not None:
                return book, f"Selected from your reading plan: {plan.title}"
        suggestions = suggest_books_for_plan(session, user=user, plan=plan, limit=1)
        if suggestions:
            book = session.get(Book, suggestions[0].book_id)
            if book is None:
                continue
            if target_session is not None and target_session.suggested_book_id is None:
                target_session.suggested_book_id = book.id
                target_session.updated_at = utc_now()
                _persist(session, target_session)
            return book, f"Selected from your reading plan: {plan.title}"
    return None
