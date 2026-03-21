from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import BedtimePack, BedtimePackItem, Book, ChildProfile, ReadingPlan, StoryDraft, User
from app.services.child_comfort_service import ChildComfortSignals, get_child_comfort_signals
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.content_lane_service import validate_content_lane_key
from app.services.i18n_service import normalize_language, validate_language_code
from app.services.parental_controls_service import AGE_BAND_ORDER, filter_books_by_parental_controls, resolve_parental_controls
from app.services.reading_plan_service import list_active_reading_plans_for_context
from app.services.recommendation_service import get_personalized_recommendations_for_user
from app.services.review_service import utc_now

BEDTIME_PACK_STATUSES = {"active", "completed", "archived"}
BEDTIME_PACK_TYPES = {"nightly", "weekend", "custom", "recovery", "reading_plan_based"}
BEDTIME_PACK_ITEM_STATUSES = {"pending", "opened", "completed", "skipped"}
SUPPORTED_AGE_BANDS = {"3-7", "8-12"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _validate_pack_status(status_value: str) -> str:
    if status_value not in BEDTIME_PACK_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported bedtime pack status")
    return status_value


def _validate_pack_type(pack_type: str) -> str:
    if pack_type not in BEDTIME_PACK_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported bedtime pack type")
    return pack_type


def _validate_item_status(status_value: str) -> str:
    if status_value not in BEDTIME_PACK_ITEM_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported bedtime pack item status")
    return status_value


def _validate_age_band(age_band: str | None) -> str | None:
    if age_band is None:
        return None
    if age_band not in SUPPORTED_AGE_BANDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported bedtime pack age band")
    return age_band


def _target_pack_size(pack_type: str) -> int:
    if pack_type == "weekend":
        return 4
    if pack_type == "recovery":
        return 2
    return 3


def _list_pack_items(session: Session, *, bedtime_pack_id: int) -> list[BedtimePackItem]:
    statement = (
        select(BedtimePackItem)
        .where(BedtimePackItem.bedtime_pack_id == bedtime_pack_id)
        .order_by(BedtimePackItem.position.asc(), BedtimePackItem.id.asc())
    )
    return list(session.exec(statement).all())


def validate_bedtime_pack_access(session: Session, *, user_id: int, pack_id: int) -> BedtimePack:
    pack = session.get(BedtimePack, pack_id)
    if pack is None or pack.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bedtime pack not found")
    return pack


def _resolve_pack_defaults(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
    language: str | None,
    age_band: str | None,
    content_lane_key: str | None,
    prefer_narration: bool,
) -> tuple[ChildProfile | None, str | None, str | None, str | None, bool, str | None]:
    child_profile = validate_child_profile_ownership(session, user_id=user.id, child_profile_id=child_profile_id)
    comfort_signals = (
        get_child_comfort_signals(session, child_profile_id=child_profile.id) if child_profile is not None else None
    )
    plans = list_active_reading_plans_for_context(
        session,
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
    )
    bedtime_plan = next(
        (
            plan
            for plan in plans
            if plan.plan_type in {"bedtime", "family_reading", "narrated", "custom"}
        ),
        None,
    )
    resolved_age_band = _validate_age_band(
        age_band
        or (child_profile.age_band if child_profile is not None else None)
        or (bedtime_plan.preferred_age_band if bedtime_plan is not None else None)
    )
    resolved_language = language or (
        comfort_signals.preferred_language if comfort_signals is not None else None
    ) or (
        child_profile.language if child_profile is not None else None
    ) or (bedtime_plan.preferred_language if bedtime_plan is not None else None) or user.language
    normalized_language = validate_language_code(resolved_language) if resolved_language else None
    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile.id if child_profile is not None else None)
    if (
        resolved_age_band is not None
        and AGE_BAND_ORDER[resolved_age_band] > AGE_BAND_ORDER[controls.max_allowed_age_band]
    ):
        resolved_age_band = controls.max_allowed_age_band
    child_default_lane = (
        child_profile.content_lane_key
        if child_profile is not None and child_profile.age_band == resolved_age_band
        else None
    )
    resolved_content_lane_key = content_lane_key or (
        bedtime_plan.preferred_content_lane_key if bedtime_plan is not None else None
    ) or child_default_lane
    if resolved_content_lane_key is not None:
        resolved_content_lane_key = validate_content_lane_key(
            session,
            age_band=resolved_age_band,
            content_lane_key=resolved_content_lane_key,
        ).key
    resolved_prefer_narration = (
        prefer_narration
        or bool(comfort_signals.prefer_narration if comfort_signals is not None else False)
        or bool(bedtime_plan.prefer_narration if bedtime_plan is not None else False)
    )
    generated_reason = bedtime_plan.title if bedtime_plan is not None else None
    return (
        child_profile,
        normalized_language,
        resolved_age_band,
        resolved_content_lane_key,
        resolved_prefer_narration,
        generated_reason,
    )


def _recent_pack_book_ids(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    before_date: date,
    lookback_days: int = 7,
) -> set[int]:
    cutoff = before_date - timedelta(days=lookback_days)
    statement = (
        select(BedtimePackItem, BedtimePack)
        .join(BedtimePack, BedtimePack.id == BedtimePackItem.bedtime_pack_id)
        .where(
            BedtimePack.user_id == user_id,
            BedtimePack.active_date != None,  # noqa: E711
            BedtimePack.active_date >= cutoff,
            BedtimePack.active_date < before_date,
            BedtimePack.status != "archived",
        )
    )
    if child_profile_id is None:
        statement = statement.where(BedtimePack.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(BedtimePack.child_profile_id == child_profile_id)
    return {item[0].book_id for item in session.exec(statement).all()}


def build_pack_candidates(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
    language: str | None,
    age_band: str | None,
    content_lane_key: str | None,
    prefer_narration: bool,
    active_date: date,
) -> list[Book]:
    (
        child_profile,
        resolved_language,
        resolved_age_band,
        resolved_content_lane_key,
        resolved_prefer_narration,
        _generated_reason,
    ) = _resolve_pack_defaults(
        session,
        user=user,
        child_profile_id=child_profile_id,
        language=language,
        age_band=age_band,
        content_lane_key=content_lane_key,
        prefer_narration=prefer_narration,
    )
    recommended_items, _ = get_personalized_recommendations_for_user(
        session,
        user=user,
        child_profile_id=child_profile.id if child_profile is not None else None,
        age_band=resolved_age_band,
        limit=12,
    )
    recommended_by_id = {item.book_id: index for index, item in enumerate(recommended_items)}
    comfort_signals = (
        get_child_comfort_signals(session, child_profile_id=child_profile.id) if child_profile is not None else None
    )

    books = list(
        session.exec(
            select(Book).where(Book.published.is_(True), Book.publication_status == "published")
        ).all()
    )
    if resolved_age_band is not None:
        books = [book for book in books if book.age_band == resolved_age_band]
    if resolved_language is not None:
        books = [book for book in books if normalize_language(book.language) == normalize_language(resolved_language)]
    if resolved_content_lane_key is not None:
        books = [book for book in books if book.content_lane_key == resolved_content_lane_key]

    controls = resolve_parental_controls(session, user=user, child_profile_id=child_profile.id if child_profile is not None else None)
    bedtime_mode_bias = bool(controls.bedtime_mode_enabled)
    books = filter_books_by_parental_controls(books, controls=controls)
    draft_ids = [book.story_draft_id for book in books if book.story_draft_id is not None]
    draft_minutes_map = (
        {
            draft.id: draft.read_time_minutes
            for draft in session.exec(select(StoryDraft).where(StoryDraft.id.in_(draft_ids))).all()
        }
        if draft_ids
        else {}
    )
    recent_ids = _recent_pack_book_ids(
        session,
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        before_date=active_date,
    )

    def candidate_score(book: Book) -> tuple[float, str]:
        score = 0.0
        if book.id in recommended_by_id:
            score += max(0, 30 - recommended_by_id[book.id] * 2)
        if bedtime_mode_bias and book.content_lane_key == "bedtime_3_7":
            score += 25
        if book.content_lane_key == "bedtime_3_7":
            score += 12
        if resolved_prefer_narration and book.audio_available:
            score += 20
        if not resolved_prefer_narration and not book.audio_available:
            score += 4
        if book.id in recent_ids:
            score -= 20
        if comfort_signals is not None:
            read_time_minutes = draft_minutes_map.get(book.story_draft_id)
            if comfort_signals.extra_calm_mode and book.content_lane_key == "bedtime_3_7":
                score += 18
            if comfort_signals.prefer_shorter_stories and read_time_minutes is not None and read_time_minutes <= 5:
                score += 12
            if "fast-paced" in comfort_signals.avoid_tags and "adventure" in (book.content_lane_key or "").lower():
                score -= 14
            if "loud" in comfort_signals.avoid_tags and "adventure" in (book.content_lane_key or "").lower():
                score -= 8
            if "spooky" in comfort_signals.avoid_tags and any(
                token in book.title.lower() for token in {"spooky", "scary", "monster", "dark"}
            ):
                score -= 10
        score += 3 if book.age_band == "3-7" else 1
        return score, book.title.lower()

    books.sort(key=lambda book: (-candidate_score(book)[0], candidate_score(book)[1], -book.id))
    return books


def choose_pack_books(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None,
    language: str | None,
    age_band: str | None,
    content_lane_key: str | None,
    prefer_narration: bool,
    active_date: date,
    pack_type: str,
) -> list[Book]:
    candidates = build_pack_candidates(
        session,
        user=user,
        child_profile_id=child_profile_id,
        language=language,
        age_band=age_band,
        content_lane_key=content_lane_key,
        prefer_narration=prefer_narration,
        active_date=active_date,
    )
    target_size = min(max(_target_pack_size(pack_type), 2), 4)
    if len(candidates) < 2:
        return candidates[: len(candidates)]
    return candidates[: min(target_size, len(candidates))]


def sequence_pack_books(
    books: list[Book],
    *,
    prefer_narration: bool,
) -> list[Book]:
    if not books:
        return []

    def energy_rank(book: Book) -> tuple[int, int, str]:
        bedtime_rank = 0 if book.content_lane_key == "bedtime_3_7" else 1
        narration_rank = 0 if prefer_narration and book.audio_available else 1
        return (bedtime_rank, narration_rank, book.title.lower())

    sorted_books = sorted(books, key=energy_rank)
    if len(sorted_books) <= 2:
        return sorted_books
    calmest = sorted_books[0]
    middle = sorted_books[1:]
    return [middle[0], *middle[1:], calmest]


def _get_existing_pack_for_date(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    active_date: date,
) -> BedtimePack | None:
    statement = (
        select(BedtimePack)
        .where(
            BedtimePack.user_id == user_id,
            BedtimePack.active_date == active_date,
            BedtimePack.status != "archived",
        )
        .order_by(BedtimePack.created_at.desc())
    )
    if child_profile_id is None:
        statement = statement.where(BedtimePack.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(BedtimePack.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def archive_old_packs(
    session: Session,
    *,
    user_id: int,
    before_date: date,
) -> int:
    rows = list(
        session.exec(
            select(BedtimePack).where(
                BedtimePack.user_id == user_id,
                BedtimePack.status == "active",
                BedtimePack.active_date != None,  # noqa: E711
                BedtimePack.active_date < before_date,
            )
        ).all()
    )
    for row in rows:
        row.status = "archived"
        row.updated_at = utc_now()
        session.add(row)
    if rows:
        session.commit()
    return len(rows)


def generate_bedtime_pack(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    title: str | None = None,
    pack_type: str = "nightly",
    language: str | None = None,
    age_band: str | None = None,
    content_lane_key: str | None = None,
    prefer_narration: bool = False,
    active_date: date | None = None,
    force_regenerate: bool = False,
) -> tuple[BedtimePack, list[BedtimePackItem], bool]:
    resolved_pack_type = _validate_pack_type(pack_type)
    resolved_active_date = active_date or utc_now().date()
    archive_old_packs(session, user_id=user.id, before_date=resolved_active_date)
    (
        child_profile,
        resolved_language,
        resolved_age_band,
        resolved_content_lane_key,
        resolved_prefer_narration,
        plan_reason,
    ) = _resolve_pack_defaults(
        session,
        user=user,
        child_profile_id=child_profile_id,
        language=language,
        age_band=age_band,
        content_lane_key=content_lane_key,
        prefer_narration=prefer_narration,
    )

    existing = _get_existing_pack_for_date(
        session,
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        active_date=resolved_active_date,
    )
    if existing is not None and not force_regenerate:
        return existing, _list_pack_items(session, bedtime_pack_id=existing.id), False

    chosen_books = choose_pack_books(
        session,
        user=user,
        child_profile_id=child_profile.id if child_profile is not None else None,
        language=resolved_language,
        age_band=resolved_age_band,
        content_lane_key=resolved_content_lane_key,
        prefer_narration=resolved_prefer_narration,
        active_date=resolved_active_date,
        pack_type=resolved_pack_type,
    )
    if len(chosen_books) < 2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enough suitable stories for a bedtime pack")
    ordered_books = sequence_pack_books(chosen_books, prefer_narration=resolved_prefer_narration)
    pack_title = title or (
        f"Buddybug Bedtime Pack for {child_profile.display_name}" if child_profile is not None else "Tonight's Calm Stories"
    )
    description = "A gentle multi-story bedtime session with a calm finish."
    generated_reason = (
        f"Built from your reading plan: {plan_reason}"
        if plan_reason is not None and resolved_pack_type == "reading_plan_based"
        else "Built for tonight's calmer story routine."
    )

    if existing is None:
        pack = BedtimePack(
            user_id=user.id,
            child_profile_id=child_profile.id if child_profile is not None else None,
            title=pack_title,
            description=description,
            status="active",
            pack_type=resolved_pack_type,
            language=resolved_language,
            age_band=resolved_age_band,
            content_lane_key=resolved_content_lane_key,
            prefer_narration=resolved_prefer_narration,
            generated_reason=generated_reason,
            active_date=resolved_active_date,
        )
    else:
        pack = existing
        pack.title = pack_title
        pack.description = description
        pack.status = "active"
        pack.pack_type = resolved_pack_type
        pack.language = resolved_language
        pack.age_band = resolved_age_band
        pack.content_lane_key = resolved_content_lane_key
        pack.prefer_narration = resolved_prefer_narration
        pack.generated_reason = generated_reason
        pack.updated_at = utc_now()
    pack = _persist(session, pack)

    for item in _list_pack_items(session, bedtime_pack_id=pack.id):
        session.delete(item)
    session.commit()

    persisted_items: list[BedtimePackItem] = []
    for index, book in enumerate(ordered_books, start=1):
        item = BedtimePackItem(
            bedtime_pack_id=pack.id,
            book_id=book.id,
            position=index,
            recommended_narration=resolved_prefer_narration and book.audio_available,
            completion_status="pending",
        )
        persisted_items.append(_persist(session, item))
    return pack, persisted_items, True


def get_or_generate_tonight_pack(
    session: Session,
    *,
    user: User,
    child_profile_id: int | None = None,
    target_date: date | None = None,
) -> tuple[BedtimePack, list[BedtimePackItem], bool]:
    resolved_target_date = target_date or utc_now().date()
    return generate_bedtime_pack(
        session,
        user=user,
        child_profile_id=child_profile_id,
        pack_type="nightly",
        active_date=resolved_target_date,
    )


def list_bedtime_packs_for_user(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    status_value: str | None,
    limit: int,
) -> list[BedtimePack]:
    statement = select(BedtimePack).where(BedtimePack.user_id == user_id)
    if child_profile_id is not None:
        statement = statement.where(BedtimePack.child_profile_id == child_profile_id)
    if status_value is not None:
        statement = statement.where(BedtimePack.status == _validate_pack_status(status_value))
    statement = statement.order_by(BedtimePack.active_date.desc(), BedtimePack.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())


def get_bedtime_pack_detail(
    session: Session,
    *,
    user: User,
    pack_id: int,
) -> tuple[BedtimePack, list[BedtimePackItem]]:
    pack = validate_bedtime_pack_access(session, user_id=user.id, pack_id=pack_id)
    return pack, _list_pack_items(session, bedtime_pack_id=pack.id)


def update_pack_item_status(
    session: Session,
    *,
    user: User,
    pack_id: int,
    item_id: int,
    completion_status: str | None = None,
    recommended_narration: bool | None = None,
) -> tuple[BedtimePackItem, BedtimePack]:
    pack = validate_bedtime_pack_access(session, user_id=user.id, pack_id=pack_id)
    item = session.get(BedtimePackItem, item_id)
    if item is None or item.bedtime_pack_id != pack.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bedtime pack item not found")
    if completion_status is not None:
        item.completion_status = _validate_item_status(completion_status)
    if recommended_narration is not None:
        item.recommended_narration = recommended_narration
    item.updated_at = utc_now()
    item = _persist(session, item)

    items = _list_pack_items(session, bedtime_pack_id=pack.id)
    if items and all(entry.completion_status in {"completed", "skipped"} for entry in items):
        pack.status = "completed"
        pack.updated_at = utc_now()
        pack = _persist(session, pack)
    return item, pack


def archive_bedtime_pack(session: Session, *, user: User, pack_id: int) -> BedtimePack:
    pack = validate_bedtime_pack_access(session, user_id=user.id, pack_id=pack_id)
    pack.status = "archived"
    pack.updated_at = utc_now()
    return _persist(session, pack)


def get_existing_pack_story_candidate(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    target_date: date,
) -> tuple[BedtimePack, BedtimePackItem] | None:
    pack = _get_existing_pack_for_date(
        session,
        user_id=user_id,
        child_profile_id=child_profile_id,
        active_date=target_date,
    )
    if pack is None:
        return None
    for item in _list_pack_items(session, bedtime_pack_id=pack.id):
        if item.completion_status in {"pending", "opened"}:
            return pack, item
    return None


def get_pack_for_book(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None,
    book_id: int,
    target_date: date | None = None,
) -> tuple[BedtimePack, list[BedtimePackItem], int] | None:
    resolved_target_date = target_date or utc_now().date()
    pack = _get_existing_pack_for_date(
        session,
        user_id=user_id,
        child_profile_id=child_profile_id,
        active_date=resolved_target_date,
    )
    if pack is None:
        return None
    items = _list_pack_items(session, bedtime_pack_id=pack.id)
    for index, item in enumerate(items):
        if item.book_id == book_id:
            return pack, items, index
    return None
