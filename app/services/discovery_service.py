from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    Book,
    BookCollection,
    BookCollectionItem,
    BookDiscoveryMetadata,
    BookTranslation,
    StoryDraft,
    StoryIdea,
    StoryPage,
    User,
)
from app.schemas.discovery_schema import (
    BookCollectionCreate,
    BookCollectionItemCreate,
    BookCollectionRead,
    BookCollectionUpdate,
    BookDiscoveryMetadataUpdate,
    CollectionDetailResponse,
    DiscoverySearchRequest,
    DiscoverySearchResponse,
    DiscoverySearchResult,
)
from app.services.child_profile_service import get_child_profile_for_user
from app.services.content_lane_service import validate_content_lane_key
from app.services.i18n_service import get_book_translation, normalize_language, validate_language_code
from app.services.parental_controls_service import filter_books_by_parental_controls, resolve_parental_controls
from app.services.reader_service import get_published_books
from app.services.review_service import utc_now
from app.utils.seed_content_lanes import BEDTIME_3_7_LANE_KEY, STORY_ADVENTURES_8_12_LANE_KEY

ADVENTURE_LEVELS = {"gentle", "moderate", "high"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _split_csv(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item and item.strip()]


def _merge_tag_strings(*values: str | None) -> str | None:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _split_csv(value):
            normalized = item.lower()
            if normalized not in seen:
                seen.add(normalized)
                items.append(item)
    return ", ".join(items) if items else None


def _draft_for_book(session: Session, *, book: Book) -> StoryDraft | None:
    return session.get(StoryDraft, book.story_draft_id)


def _story_idea_for_draft(session: Session, *, draft: StoryDraft | None) -> StoryIdea | None:
    if draft is None or draft.story_idea_id is None:
        return None
    return session.get(StoryIdea, draft.story_idea_id)


def _story_pages_for_draft(session: Session, *, story_draft_id: int) -> list[StoryPage]:
    return list(
        session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft_id).order_by(StoryPage.page_number)).all()
    )


def _translation_titles_and_descriptions(session: Session, *, book_id: int) -> str:
    translations = list(session.exec(select(BookTranslation).where(BookTranslation.book_id == book_id)).all())
    chunks: list[str] = []
    for translation in translations:
        chunks.extend(part for part in [translation.title, translation.description] if part)
    return " ".join(chunks)


def _derive_character_tags(story_pages: list[StoryPage], story_idea: StoryIdea | None) -> str | None:
    page_values = ", ".join(page.characters_present for page in story_pages if page.characters_present)
    return _merge_tag_strings(
        page_values,
        story_idea.main_characters if story_idea is not None else None,
        story_idea.supporting_characters if story_idea is not None else None,
    )


def _mode_tags(lane_key: str | None, story_idea: StoryIdea | None, draft: StoryDraft | None) -> list[str]:
    normalized_tone = _normalize_text(story_idea.tone if story_idea is not None else None)
    summary = _normalize_text(draft.summary if draft is not None else None)
    tags: list[str] = ["plot-led", "story-led"]
    if lane_key == BEDTIME_3_7_LANE_KEY:
        tags.extend(["gentle", "young-reader"])
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        tags.extend(["adventure", "older-reader"])
    if any(token in normalized_tone for token in ["calm", "gentle", "bedtime", "sleepy", "soothing"]):
        tags.extend(["calm", "bedtime"])
    if any(token in normalized_tone for token in ["playful", "cheeky", "mischief", "fun"]):
        tags.extend(["playful", "cheeky"])
    if any(token in summary for token in ["mystery", "problem", "missing", "muddle", "clue", "solution"]):
        tags.append("story-driven")
    return tags


def _derive_tone_tags(
    book: Book,
    draft: StoryDraft | None,
    story_idea: StoryIdea | None,
    story_pages: list[StoryPage],
) -> str | None:
    page_moods = ", ".join(page.mood for page in story_pages if page.mood)
    return _merge_tag_strings(
        page_moods,
        story_idea.tone if story_idea is not None else None,
        draft.summary if draft is not None else None,
        ", ".join(_mode_tags(book.content_lane_key, story_idea, draft)),
    )


def _derive_theme_tags(story_idea: StoryIdea | None, draft: StoryDraft | None) -> str | None:
    return _merge_tag_strings(
        story_idea.theme if story_idea is not None else None,
        story_idea.bedtime_feeling if story_idea is not None else None,
        draft.summary if draft is not None else None,
    )


def _derive_setting_tags(story_idea: StoryIdea | None, story_pages: list[StoryPage]) -> str | None:
    page_locations = ", ".join(page.location for page in story_pages if page.location)
    return _merge_tag_strings(story_idea.setting if story_idea is not None else None, page_locations)


def _derive_style_tags(book: Book, story_idea: StoryIdea | None, draft: StoryDraft | None) -> str | None:
    values: list[str] = []
    if book.content_lane_key == BEDTIME_3_7_LANE_KEY:
        values.append("calming")
        values.append("bedtime")
        values.append("story-driven")
    if book.content_lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        values.append("adventure")
        values.append("story-driven")
    normalized_tone = _normalize_text(story_idea.tone if story_idea is not None else None)
    if any(token in normalized_tone for token in ["playful", "cheeky", "mischief", "fun"]):
        values.extend(["playful", "cheeky"])
    if any(token in normalized_tone for token in ["calm", "gentle", "bedtime", "sleepy", "soothing"]):
        values.extend(["calm", "bedtime"])
    if story_idea is not None and story_idea.age_band == "8-12":
        values.append("older-reader")
    if draft is not None and draft.generation_source == "manual":
        values.append("editorial")
    return _merge_tag_strings(", ".join(values))


def _derive_bedtime_safe(book: Book, story_idea: StoryIdea | None) -> bool:
    if book.content_lane_key == BEDTIME_3_7_LANE_KEY:
        normalized_tone = _normalize_text(story_idea.tone if story_idea is not None else None)
        return not any(token in normalized_tone for token in ["cheeky", "mischief"])
    if story_idea is not None and "calm" in _normalize_text(story_idea.tone):
        return True
    return False


def _derive_adventure_level(book: Book, story_idea: StoryIdea | None) -> str | None:
    if book.content_lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return "high"
    if story_idea is not None:
        normalized_tone = _normalize_text(story_idea.tone)
        if any(token in normalized_tone for token in ["playful", "cheeky", "mischief", "fun"]):
            return "moderate"
        if "adventur" in normalized_tone:
            return "moderate"
        if "calm" in normalized_tone or "gentle" in normalized_tone:
            return "gentle"
    return "gentle" if book.content_lane_key == BEDTIME_3_7_LANE_KEY else None


def _build_searchable_text(
    *,
    book: Book,
    draft: StoryDraft | None,
    story_idea: StoryIdea | None,
    story_pages: list[StoryPage],
    translated_text: str,
) -> tuple[str, str | None, str | None]:
    summary = (draft.summary if draft is not None else None) or (story_idea.premise if story_idea is not None else None)
    page_excerpt = " ".join(page.page_text for page in story_pages[:4])
    text = " ".join(
        part
        for part in [
            book.title,
            summary,
            page_excerpt,
            translated_text,
            story_idea.premise if story_idea is not None else None,
            story_idea.theme if story_idea is not None else None,
        ]
        if part
    )
    return _normalize_text(book.title), summary, _normalize_text(text)


def get_book_discovery_metadata(session: Session, *, book_id: int) -> BookDiscoveryMetadata | None:
    return session.exec(select(BookDiscoveryMetadata).where(BookDiscoveryMetadata.book_id == book_id)).first()


def build_book_discovery_metadata(session: Session, *, book_id: int) -> BookDiscoveryMetadata:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    draft = _draft_for_book(session, book=book)
    story_idea = _story_idea_for_draft(session, draft=draft)
    story_pages = _story_pages_for_draft(session, story_draft_id=draft.id) if draft is not None else []
    translated_text = _translation_titles_and_descriptions(session, book_id=book.id)
    searchable_title, searchable_summary, searchable_text = _build_searchable_text(
        book=book,
        draft=draft,
        story_idea=story_idea,
        story_pages=story_pages,
        translated_text=translated_text,
    )
    existing = get_book_discovery_metadata(session, book_id=book.id)
    if existing is None:
        existing = BookDiscoveryMetadata(book_id=book.id, searchable_title=searchable_title)
    existing.searchable_title = searchable_title
    existing.searchable_summary = searchable_summary
    existing.searchable_text = searchable_text
    existing.age_band = book.age_band
    existing.language = book.language
    existing.content_lane_key = book.content_lane_key
    existing.tone_tags = _derive_tone_tags(book, draft, story_idea, story_pages)
    existing.theme_tags = _derive_theme_tags(story_idea, draft)
    existing.character_tags = _derive_character_tags(story_pages, story_idea)
    existing.setting_tags = _derive_setting_tags(story_idea, story_pages)
    existing.style_tags = _derive_style_tags(book, story_idea, draft)
    existing.bedtime_safe = _derive_bedtime_safe(book, story_idea)
    existing.adventure_level = _derive_adventure_level(book, story_idea)
    if existing.is_featured is None:
        existing.is_featured = False
    existing.updated_at = utc_now()
    return _persist(session, existing)


def rebuild_book_discovery_metadata(session: Session, *, book_id: int) -> BookDiscoveryMetadata:
    return build_book_discovery_metadata(session, book_id=book_id)


def rebuild_all_discovery_metadata(session: Session) -> list[BookDiscoveryMetadata]:
    books = list(session.exec(select(Book).order_by(Book.created_at.asc())).all())
    return [build_book_discovery_metadata(session, book_id=book.id) for book in books]


def update_book_discovery_metadata(
    session: Session,
    *,
    metadata: BookDiscoveryMetadata,
    payload: BookDiscoveryMetadataUpdate,
) -> BookDiscoveryMetadata:
    update_data = payload.model_dump(exclude_unset=True)
    if "language" in update_data and update_data["language"] is not None:
        update_data["language"] = validate_language_code(update_data["language"])
    if "content_lane_key" in update_data and update_data["content_lane_key"] is not None:
        update_data["content_lane_key"] = validate_content_lane_key(
            session,
            age_band=update_data.get("age_band") or metadata.age_band,
            content_lane_key=update_data["content_lane_key"],
        ).key
    if "age_band" in update_data and update_data["age_band"] is not None:
        if update_data["age_band"] not in {"3-7", "8-12"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported age band")
    if "adventure_level" in update_data and update_data["adventure_level"] is not None:
        if update_data["adventure_level"] not in ADVENTURE_LEVELS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported adventure level")
    for field_name, value in update_data.items():
        setattr(metadata, field_name, value)
    metadata.updated_at = utc_now()
    return _persist(session, metadata)


def _resolve_controls_and_context(
    session: Session,
    *,
    current_user: User | None,
    child_profile_id: int | None,
):
    child_profile = None
    controls = None
    if current_user is not None:
        child_profile = (
            get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)
            if child_profile_id is not None
            else None
        )
        controls = resolve_parental_controls(
            session,
            user=current_user,
            child_profile_id=child_profile.id if child_profile is not None else None,
        )
    return child_profile, controls


def _matches_query(metadata: BookDiscoveryMetadata, query: str | None) -> tuple[bool, list[str]]:
    if not query:
        return True, []
    normalized_query = _normalize_text(query)
    reasons: list[str] = []
    if normalized_query in (metadata.searchable_title or ""):
        reasons.append("title match")
    if normalized_query in (metadata.searchable_summary or "").lower():
        reasons.append("summary match")
    if normalized_query in (metadata.searchable_text or ""):
        reasons.append("catalog text match")
    return bool(reasons), reasons


def _matches_tag(value: str | None, needle: str | None) -> bool:
    if needle is None:
        return True
    return needle.strip().lower() in {item.lower() for item in _split_csv(value)}


def _score_result(
    *,
    metadata: BookDiscoveryMetadata,
    book: Book,
    query: str | None,
    requested_language: str | None,
    bedtime_bias: bool,
    base_reasons: list[str],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons = list(base_reasons)
    normalized_query = _normalize_text(query) if query else None
    if normalized_query and metadata.searchable_title.startswith(normalized_query):
        score += 5.0
        reasons.append("starts with title match")
    if normalized_query and normalized_query == metadata.searchable_title:
        score += 6.0
        reasons.append("exact title match")
    if normalized_query and normalized_query in (metadata.searchable_text or ""):
        score += 2.0
    if requested_language and normalize_language(requested_language) == book.language:
        score += 1.5
        reasons.append("language match")
    if metadata.is_featured:
        score += 1.0
        reasons.append("featured")
    if bedtime_bias and metadata.bedtime_safe:
        score += 2.0
        reasons.append("bedtime-safe")
    tone_tags = {item.lower() for item in _split_csv(metadata.tone_tags)}
    style_tags = {item.lower() for item in _split_csv(metadata.style_tags)}
    if bedtime_bias and (tone_tags.intersection({"calm", "gentle", "bedtime"}) or style_tags.intersection({"calm", "bedtime"})):
        score += 1.5
        reasons.append("extra calm fit")
    if not bedtime_bias and (
        tone_tags.intersection({"playful", "cheeky"}) or style_tags.intersection({"playful", "cheeky"})
    ):
        score += 1.0
        reasons.append("playful daytime fit")
    if book.content_lane_key == BEDTIME_3_7_LANE_KEY:
        score += 0.5
    return score, list(dict.fromkeys(reasons))


def _ensure_metadata_for_books(session: Session, *, books: list[Book]) -> dict[int, BookDiscoveryMetadata]:
    if not books:
        return {}
    metadata_rows = list(
        session.exec(select(BookDiscoveryMetadata).where(BookDiscoveryMetadata.book_id.in_([book.id for book in books]))).all()
    )
    metadata_by_book_id = {row.book_id: row for row in metadata_rows}
    for book in books:
        if book.id not in metadata_by_book_id:
            metadata_by_book_id[book.id] = build_book_discovery_metadata(session, book_id=book.id)
    return metadata_by_book_id


def _display_title(session: Session, *, book: Book, requested_language: str | None) -> str:
    if requested_language:
        translation = get_book_translation(session, book_id=book.id, language=normalize_language(requested_language))
        if translation is not None:
            return translation.title
    return book.title


def _search_candidates(
    session: Session,
    *,
    published_only: bool,
    limit: int | None = None,
) -> list[Book]:
    if published_only:
        return get_published_books(session, age_band=None, content_lane_key=None, language=None, limit=limit or 500)
    statement = select(Book).order_by(Book.updated_at.desc())
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


def search_books(
    session: Session,
    *,
    request: DiscoverySearchRequest,
    current_user: User | None = None,
    child_profile_id: int | None = None,
    published_only: bool = True,
) -> DiscoverySearchResponse:
    child_profile, controls = _resolve_controls_and_context(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    requested_language = child_profile.language if child_profile is not None else request.language
    effective_age_band = child_profile.age_band if child_profile is not None else request.age_band
    candidate_books = _search_candidates(session, published_only=published_only, limit=600)
    if effective_age_band:
        candidate_books = [book for book in candidate_books if book.age_band == effective_age_band]
    if request.content_lane_key:
        candidate_books = [book for book in candidate_books if book.content_lane_key == request.content_lane_key]
    if requested_language:
        requested_language = normalize_language(requested_language)
        candidate_books = [book for book in candidate_books if book.language == requested_language]
    if controls is not None:
        candidate_books = filter_books_by_parental_controls(candidate_books, controls=controls)

    metadata_by_book_id = _ensure_metadata_for_books(session, books=candidate_books)
    items: list[DiscoverySearchResult] = []
    bedtime_bias = bool(controls is not None and controls.bedtime_mode_enabled)
    for book in candidate_books:
        metadata = metadata_by_book_id[book.id]
        if request.featured_only and not metadata.is_featured:
            continue
        if request.bedtime_safe is not None and metadata.bedtime_safe != request.bedtime_safe:
            continue
        if not _matches_tag(metadata.tone_tags, request.tone_tag):
            continue
        if not _matches_tag(metadata.character_tags, request.character_tag):
            continue
        matches_query, query_reasons = _matches_query(metadata, request.q)
        if not matches_query:
            continue
        score, reasons = _score_result(
            metadata=metadata,
            book=book,
            query=request.q,
            requested_language=requested_language,
            bedtime_bias=bedtime_bias,
            base_reasons=query_reasons,
        )
        items.append(
            DiscoverySearchResult(
                book_id=book.id,
                title=_display_title(session, book=book, requested_language=requested_language),
                cover_image_url=book.cover_image_url,
                age_band=book.age_band,
                language=book.language,
                content_lane_key=book.content_lane_key,
                published=book.published,
                publication_status=book.publication_status,
                score=round(score, 2),
                reasons=reasons or None,
            )
        )
    items.sort(key=lambda item: ((item.score or 0), item.title.casefold()), reverse=True)
    total = len(items)
    paged = items[request.offset : request.offset + request.limit]
    return DiscoverySearchResponse(total=total, items=paged)


def list_featured_books(
    session: Session,
    *,
    age_band: str | None,
    language: str | None,
    content_lane_key: str | None,
    limit: int,
    current_user: User | None = None,
    child_profile_id: int | None = None,
) -> DiscoverySearchResponse:
    return search_books(
        session,
        request=DiscoverySearchRequest(
            age_band=age_band,
            language=language,
            content_lane_key=content_lane_key,
            featured_only=True,
            limit=limit,
        ),
        current_user=current_user,
        child_profile_id=child_profile_id,
        published_only=True,
    )


def list_collections(
    session: Session,
    *,
    age_band: str | None,
    language: str | None,
    content_lane_key: str | None,
    featured_only: bool,
    public_only: bool,
) -> list[BookCollection]:
    statement = select(BookCollection).order_by(BookCollection.updated_at.desc(), BookCollection.title.asc())
    if public_only:
        statement = statement.where(BookCollection.is_public.is_(True))
    if age_band is not None:
        statement = statement.where((BookCollection.age_band == age_band) | (BookCollection.age_band == None))  # noqa: E711
    if language is not None:
        normalized_language = normalize_language(language)
        statement = statement.where((BookCollection.language == normalized_language) | (BookCollection.language == None))  # noqa: E711
    if content_lane_key is not None:
        statement = statement.where((BookCollection.content_lane_key == content_lane_key) | (BookCollection.content_lane_key == None))  # noqa: E711
    if featured_only:
        statement = statement.where(BookCollection.is_featured.is_(True))
    return list(session.exec(statement).all())


def get_collection_or_404(session: Session, *, collection_key: str, public_only: bool) -> BookCollection:
    statement = select(BookCollection).where(BookCollection.key == collection_key)
    if public_only:
        statement = statement.where(BookCollection.is_public.is_(True))
    collection = session.exec(statement).first()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection


def get_collection_detail(
    session: Session,
    *,
    collection_key: str,
    current_user: User | None = None,
    child_profile_id: int | None = None,
    public_only: bool = True,
) -> CollectionDetailResponse:
    collection = get_collection_or_404(session, collection_key=collection_key, public_only=public_only)
    collection_items = list(
        session.exec(
            select(BookCollectionItem)
            .where(BookCollectionItem.collection_id == collection.id)
            .order_by(BookCollectionItem.position.asc(), BookCollectionItem.created_at.asc())
        ).all()
    )
    books = [session.get(Book, item.book_id) for item in collection_items]
    books = [book for book in books if book is not None]
    if public_only:
        books = [book for book in books if book.published and book.publication_status == "published"]
    child_profile, controls = _resolve_controls_and_context(
        session,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    requested_language = child_profile.language if child_profile is not None else collection.language
    if controls is not None:
        books = filter_books_by_parental_controls(books, controls=controls)
    metadata_by_book_id = _ensure_metadata_for_books(session, books=books)
    result_by_book_id: dict[int, DiscoverySearchResult] = {}
    bedtime_bias = bool(controls is not None and controls.bedtime_mode_enabled)
    for book in books:
        metadata = metadata_by_book_id[book.id]
        score, reasons = _score_result(
            metadata=metadata,
            book=book,
            query=None,
            requested_language=requested_language,
            bedtime_bias=bedtime_bias,
            base_reasons=["collection match"],
        )
        result_by_book_id[book.id] = DiscoverySearchResult(
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
    ordered_items = [result_by_book_id[item.book_id] for item in collection_items if item.book_id in result_by_book_id]
    return CollectionDetailResponse(collection=BookCollectionRead.model_validate(collection), items=ordered_items)


def create_collection(session: Session, *, payload: BookCollectionCreate, created_by_user_id: int | None) -> BookCollection:
    existing = session.exec(select(BookCollection).where(BookCollection.key == payload.key)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection key already exists")
    if payload.language is not None:
        language = validate_language_code(payload.language)
    else:
        language = None
    age_band = payload.age_band
    if age_band is not None and age_band not in {"3-7", "8-12"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported age band")
    content_lane_key = None
    if payload.content_lane_key is not None:
        content_lane_key = validate_content_lane_key(
            session,
            age_band=age_band,
            content_lane_key=payload.content_lane_key,
        ).key
    collection = BookCollection(
        key=payload.key,
        title=payload.title,
        description=payload.description,
        language=language,
        age_band=age_band,
        content_lane_key=content_lane_key,
        is_public=payload.is_public,
        is_featured=payload.is_featured,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, collection)


def update_collection(session: Session, *, collection: BookCollection, payload: BookCollectionUpdate) -> BookCollection:
    update_data = payload.model_dump(exclude_unset=True)
    if "key" in update_data and update_data["key"] is not None and update_data["key"] != collection.key:
        existing = session.exec(select(BookCollection).where(BookCollection.key == update_data["key"])).first()
        if existing is not None and existing.id != collection.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection key already exists")
    if "language" in update_data and update_data["language"] is not None:
        update_data["language"] = validate_language_code(update_data["language"])
    if "age_band" in update_data and update_data["age_band"] is not None and update_data["age_band"] not in {"3-7", "8-12"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported age band")
    if "content_lane_key" in update_data and update_data["content_lane_key"] is not None:
        update_data["content_lane_key"] = validate_content_lane_key(
            session,
            age_band=update_data.get("age_band") or collection.age_band,
            content_lane_key=update_data["content_lane_key"],
        ).key
    for field_name, value in update_data.items():
        setattr(collection, field_name, value)
    collection.updated_at = utc_now()
    return _persist(session, collection)


def delete_collection(session: Session, *, collection: BookCollection) -> None:
    items = list(session.exec(select(BookCollectionItem).where(BookCollectionItem.collection_id == collection.id)).all())
    for item in items:
        session.delete(item)
    session.delete(collection)
    session.commit()


def add_collection_item(session: Session, *, collection: BookCollection, payload: BookCollectionItemCreate) -> BookCollectionItem:
    book = session.get(Book, payload.book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    existing = session.exec(
        select(BookCollectionItem).where(
            BookCollectionItem.collection_id == collection.id,
            BookCollectionItem.book_id == payload.book_id,
        )
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is already in this collection")
    item = BookCollectionItem(collection_id=collection.id, book_id=payload.book_id, position=payload.position)
    return _persist(session, item)


def get_collection_item_or_404(session: Session, *, item_id: int) -> BookCollectionItem:
    item = session.get(BookCollectionItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection item not found")
    return item


def update_collection_item(session: Session, *, item: BookCollectionItem, position: int | None) -> BookCollectionItem:
    if position is not None:
        item.position = position
    item.updated_at = utc_now()
    return _persist(session, item)


def delete_collection_item(session: Session, *, item: BookCollectionItem) -> None:
    session.delete(item)
    session.commit()
