from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, SeasonalCampaign, SeasonalCampaignItem, User
from app.schemas.discovery_schema import DiscoverySearchResult
from app.schemas.seasonal_campaign_schema import (
    SeasonalCampaignCreate,
    SeasonalCampaignDetailResponse,
    SeasonalCampaignRead,
    SeasonalCampaignUpdate,
    SeasonalCampaignItemCreate,
)
from app.services.content_lane_service import validate_content_lane_key
from app.services.discovery_service import (
    _display_title,
    _ensure_metadata_for_books,
    _resolve_controls_and_context,
    _score_result,
)
from app.services.i18n_service import normalize_language, validate_language_code
from app.services.parental_controls_service import filter_books_by_parental_controls
from app.services.review_service import utc_now


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def get_campaign_or_404(
    session: Session,
    *,
    campaign_id: int | None = None,
    campaign_key: str | None = None,
) -> SeasonalCampaign:
    if campaign_id is not None:
        campaign = session.get(SeasonalCampaign, campaign_id)
    else:
        campaign = session.exec(select(SeasonalCampaign).where(SeasonalCampaign.key == campaign_key)).first()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


def get_campaign_item_or_404(session: Session, *, item_id: int) -> SeasonalCampaignItem:
    item = session.get(SeasonalCampaignItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign item not found")
    return item


def list_campaigns_for_admin(session: Session) -> list[SeasonalCampaign]:
    return list(
        session.exec(select(SeasonalCampaign).order_by(SeasonalCampaign.updated_at.desc(), SeasonalCampaign.title.asc())).all()
    )


def get_active_campaigns(
    session: Session,
    *,
    language: str | None,
    age_band: str | None,
    content_lane_key: str | None,
    current_user: User | None = None,
    child_profile_id: int | None = None,
) -> list[SeasonalCampaign]:
    child_profile, controls = _resolve_controls_and_context(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    effective_language = child_profile.language if child_profile is not None else language
    effective_age_band = child_profile.age_band if child_profile is not None else age_band
    effective_lane = content_lane_key
    if child_profile is not None and child_profile.content_lane_key:
        effective_lane = child_profile.content_lane_key

    now = utc_now()
    statement = (
        select(SeasonalCampaign)
        .where(
            SeasonalCampaign.is_active.is_(True),
            SeasonalCampaign.start_at <= now,
            SeasonalCampaign.end_at >= now,
        )
        .order_by(SeasonalCampaign.start_at.desc(), SeasonalCampaign.title.asc())
    )
    campaigns = list(session.exec(statement).all())

    if effective_language is not None:
        normalized_language = normalize_language(effective_language)
        campaigns = [campaign for campaign in campaigns if campaign.language in {None, normalized_language}]
    if effective_age_band is not None:
        campaigns = [campaign for campaign in campaigns if campaign.age_band in {None, effective_age_band}]
    if effective_lane is not None:
        campaigns = [campaign for campaign in campaigns if campaign.content_lane_key in {None, effective_lane}]
    if controls is not None and controls.max_allowed_age_band == "3-7":
        campaigns = [campaign for campaign in campaigns if campaign.age_band in {None, "3-7"}]
    return campaigns


def get_active_campaign_for_home(
    session: Session,
    *,
    language: str | None,
    age_band: str | None,
    content_lane_key: str | None,
    current_user: User | None = None,
    child_profile_id: int | None = None,
) -> SeasonalCampaign | None:
    campaigns = get_active_campaigns(
        session,
        language=language,
        age_band=age_band,
        content_lane_key=content_lane_key,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    for campaign in campaigns:
        if campaign.homepage_cta_route or campaign.homepage_badge_text:
            return campaign
    return campaigns[0] if campaigns else None


def get_campaign_detail(
    session: Session,
    *,
    campaign_key: str,
    current_user: User | None = None,
    child_profile_id: int | None = None,
    active_only: bool = True,
) -> SeasonalCampaignDetailResponse:
    campaign = get_campaign_or_404(session, campaign_key=campaign_key)
    now = utc_now()
    if active_only and (not campaign.is_active or campaign.start_at > now or campaign.end_at < now):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    items = list(
        session.exec(
            select(SeasonalCampaignItem)
            .where(SeasonalCampaignItem.campaign_id == campaign.id)
            .order_by(SeasonalCampaignItem.position.asc(), SeasonalCampaignItem.created_at.asc())
        ).all()
    )
    books = [session.get(Book, item.book_id) for item in items]
    books = [book for book in books if book is not None and book.published and book.publication_status == "published"]

    child_profile, controls = _resolve_controls_and_context(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    requested_language = child_profile.language if child_profile is not None else campaign.language
    if controls is not None:
        books = filter_books_by_parental_controls(books, controls=controls)
    metadata_by_book_id = _ensure_metadata_for_books(session, books=books)
    bedtime_bias = bool(controls is not None and controls.bedtime_mode_enabled)
    results_by_book_id: dict[int, DiscoverySearchResult] = {}
    for book in books:
        metadata = metadata_by_book_id[book.id]
        score, reasons = _score_result(
            metadata=metadata,
            book=book,
            query=None,
            requested_language=requested_language,
            bedtime_bias=bedtime_bias,
            base_reasons=["seasonal campaign"],
        )
        results_by_book_id[book.id] = DiscoverySearchResult(
            book_id=book.id,
            title=_display_title(session, book=book, requested_language=requested_language),
            cover_image_url=book.cover_image_url,
            age_band=book.age_band,
            language=book.language,
            content_lane_key=book.content_lane_key,
            published=book.published,
            publication_status=book.publication_status,
            score=round(score, 2),
            reasons=reasons,
        )
    ordered = [results_by_book_id[item.book_id] for item in items if item.book_id in results_by_book_id]
    return SeasonalCampaignDetailResponse(campaign=SeasonalCampaignRead.model_validate(campaign), items=ordered)


def create_campaign(
    session: Session,
    *,
    payload: SeasonalCampaignCreate,
    created_by_user_id: int | None,
) -> SeasonalCampaign:
    existing = session.exec(select(SeasonalCampaign).where(SeasonalCampaign.key == payload.key)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign key already exists")
    language = validate_language_code(payload.language) if payload.language is not None else None
    age_band = _validate_age_band(payload.age_band)
    content_lane_key = _validate_lane(session, age_band=age_band, content_lane_key=payload.content_lane_key)
    start_at = _normalize_datetime(payload.start_at)
    end_at = _normalize_datetime(payload.end_at)
    if end_at <= start_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign end_at must be after start_at")
    campaign = SeasonalCampaign(
        key=payload.key,
        title=payload.title,
        description=payload.description,
        start_at=start_at,
        end_at=end_at,
        is_active=payload.is_active,
        language=language,
        age_band=age_band,
        content_lane_key=content_lane_key,
        homepage_badge_text=payload.homepage_badge_text,
        homepage_cta_label=payload.homepage_cta_label,
        homepage_cta_route=payload.homepage_cta_route,
        banner_style_key=payload.banner_style_key,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, campaign)


def update_campaign(session: Session, *, campaign: SeasonalCampaign, payload: SeasonalCampaignUpdate) -> SeasonalCampaign:
    update_data = payload.model_dump(exclude_unset=True)
    if "key" in update_data and update_data["key"] is not None and update_data["key"] != campaign.key:
        existing = session.exec(select(SeasonalCampaign).where(SeasonalCampaign.key == update_data["key"])).first()
        if existing is not None and existing.id != campaign.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign key already exists")
    if "language" in update_data and update_data["language"] is not None:
        update_data["language"] = validate_language_code(update_data["language"])
    if "age_band" in update_data:
        update_data["age_band"] = _validate_age_band(update_data["age_band"])
    if "content_lane_key" in update_data:
        update_data["content_lane_key"] = _validate_lane(
            session,
            age_band=update_data.get("age_band") or campaign.age_band,
            content_lane_key=update_data["content_lane_key"],
        )
    start_at = _normalize_datetime(update_data["start_at"]) if update_data.get("start_at") is not None else campaign.start_at
    end_at = _normalize_datetime(update_data["end_at"]) if update_data.get("end_at") is not None else campaign.end_at
    if end_at <= start_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign end_at must be after start_at")
    update_data["start_at"] = start_at
    update_data["end_at"] = end_at
    for field_name, value in update_data.items():
        setattr(campaign, field_name, value)
    campaign.updated_at = utc_now()
    return _persist(session, campaign)


def delete_campaign(session: Session, *, campaign: SeasonalCampaign) -> None:
    items = list(session.exec(select(SeasonalCampaignItem).where(SeasonalCampaignItem.campaign_id == campaign.id)).all())
    for item in items:
        session.delete(item)
    session.delete(campaign)
    session.commit()


def add_campaign_item(
    session: Session,
    *,
    campaign: SeasonalCampaign,
    payload: SeasonalCampaignItemCreate,
) -> SeasonalCampaignItem:
    book = session.get(Book, payload.book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    existing = session.exec(
        select(SeasonalCampaignItem).where(
            SeasonalCampaignItem.campaign_id == campaign.id,
            SeasonalCampaignItem.book_id == payload.book_id,
        )
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is already in this campaign")
    item = SeasonalCampaignItem(campaign_id=campaign.id, book_id=payload.book_id, position=payload.position)
    return _persist(session, item)


def remove_campaign_item(session: Session, *, item: SeasonalCampaignItem) -> None:
    session.delete(item)
    session.commit()


def _validate_age_band(age_band: str | None) -> str | None:
    if age_band is None:
        return None
    if age_band not in {"3-7", "8-12"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported age band")
    return age_band


def _validate_lane(session: Session, *, age_band: str | None, content_lane_key: str | None) -> str | None:
    if content_lane_key is None:
        return None
    return validate_content_lane_key(session, age_band=age_band, content_lane_key=content_lane_key).key
