from __future__ import annotations

import json
import math
import re

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, BookPage, ClassicAdaptationDraft, ClassicSource, Illustration, StoryDraft, StoryPage, User
from app.services.classic_adaptation_service import adapt_classic_source
from app.services.classic_prompt_templates import (
    ClassicSceneSeedNote,
    build_classic_illustration_prompt,
    validate_classic_adaptation_intensity,
)
from app.services.content_lane_service import validate_content_lane_key
from app.services.editorial_service import build_preview_book, create_editorial_project
from app.services.i18n_service import validate_language_code
from app.services.narration_service import auto_generate_default_narration_for_book
from app.services.review_service import utc_now
from app.services.story_quality_service import evaluate_illustration_quality
from app.services.illustration_planner import generate_story_page_payloads
from app.services.illustration_generator import generate_illustration_asset
from app.services.book_builder import validate_story_pages_ready_for_release

CLASSIC_SOURCE_STATUSES = {"imported", "drafted", "illustrated", "approved", "published", "archived"}
CLASSIC_DRAFT_REVIEW_STATUSES = {"pending", "approved", "rejected", "archived"}
CLASSIC_DRAFT_ILLUSTRATION_STATUSES = {"not_started", "pages_planned", "illustrated", "published", "archived"}
CLASSIC_VALIDATION_STATUSES = {"accepted", "accepted_with_warnings", "rejected"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_classic_source_status(value: str) -> str:
    if value not in CLASSIC_SOURCE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid classic source status")
    return value


def validate_classic_draft_review_status(value: str) -> str:
    if value not in CLASSIC_DRAFT_REVIEW_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid classic draft review status")
    return value


def validate_classic_draft_illustration_status(value: str) -> str:
    if value not in CLASSIC_DRAFT_ILLUSTRATION_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid classic illustration status")
    return value


def validate_classic_validation_status(value: str) -> str:
    if value not in CLASSIC_VALIDATION_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid classic validation status")
    return value


def validate_classic_adaptation_intensity_or_400(value: str | None) -> str:
    try:
        return validate_classic_adaptation_intensity(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid classic adaptation intensity") from exc


def get_classic_source_or_404(session: Session, classic_source_id: int) -> ClassicSource:
    classic_source = session.get(ClassicSource, classic_source_id)
    if classic_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classic source not found")
    return classic_source


def get_classic_adaptation_or_404(session: Session, classic_adaptation_draft_id: int) -> ClassicAdaptationDraft:
    classic_draft = session.get(ClassicAdaptationDraft, classic_adaptation_draft_id)
    if classic_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classic adaptation draft not found")
    return classic_draft


def list_classic_sources(
    session: Session,
    *,
    status_value: str | None,
    limit: int,
) -> list[ClassicSource]:
    statement = select(ClassicSource).order_by(ClassicSource.updated_at.desc()).limit(limit)
    if status_value is not None:
        statement = statement.where(ClassicSource.import_status == validate_classic_source_status(status_value))
    return list(session.exec(statement).all())


def list_classic_adaptations(
    session: Session,
    *,
    classic_source_id: int | None,
    review_status: str | None,
    limit: int,
) -> list[ClassicAdaptationDraft]:
    statement = select(ClassicAdaptationDraft).order_by(ClassicAdaptationDraft.updated_at.desc()).limit(limit)
    if classic_source_id is not None:
        statement = statement.where(ClassicAdaptationDraft.classic_source_id == classic_source_id)
    if review_status is not None:
        statement = statement.where(
            ClassicAdaptationDraft.review_status == validate_classic_draft_review_status(review_status)
        )
    return list(session.exec(statement).all())


def _normalized_title_key(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "classic"


def _build_project_slug(session: Session, title: str) -> str:
    base = f"classic-{_slugify(title)}"
    candidate = base
    suffix = 2
    from app.models import EditorialProject

    while session.exec(select(EditorialProject).where(EditorialProject.slug == candidate)).first() is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _story_summary(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:280] if compact else "Classic adaptation draft"


def _read_time_minutes(text: str) -> int:
    return max(4, math.ceil(max(len(text.split()), 1) / 140))


def _parse_scene_seed_notes(scene_seed_notes_json: str | None) -> list[ClassicSceneSeedNote]:
    if not scene_seed_notes_json:
        return []
    try:
        payload = json.loads(scene_seed_notes_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    notes: list[ClassicSceneSeedNote] = []
    for item in payload:
        try:
            notes.append(ClassicSceneSeedNote.model_validate(item))
        except Exception:
            continue
    return notes


def _infer_classic_location(page_text: str, fallback: str | None = None) -> str:
    lowered = page_text.casefold()
    rules: list[tuple[str, tuple[str, ...]]] = [
        ("bears' forest cottage", ("bear", "porridge", "chair", "cottage", "little house")),
        ("woodland path", ("wolf", "woods", "wood", "path", "forest", "trail")),
        ("grandmother's cottage", ("grandmamma", "grandmother", "bobbin", "latch")),
        ("royal bedchamber", ("princess", "pea", "mattress", "mattresses", "bedstead", "quilt")),
        ("palace hall or museum", ("museum", "prince took her", "true princess")),
        ("shoemaker's workshop", ("shoemaker", "shoe", "shoes", "leather", "table")),
        ("farmyard and riverside", ("duckling", "duck", "farmyard", "river", "moor", "swans")),
        ("fairytale meadow", ("meadow", "field", "grass", "hill")),
    ]
    for label, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            return label
    cleaned_fallback = (fallback or "").strip()
    if cleaned_fallback and cleaned_fallback.casefold() not in {"cozy bedroom", "moonlit garden"}:
        return cleaned_fallback
    return "classic story setting"


def _infer_classic_mood(page_text: str, fallback: str | None = None) -> str:
    lowered = page_text.casefold()
    rules: list[tuple[str, tuple[str, ...]]] = [
        ("tense but child-safe", ("storm", "thunder", "fearful", "wolf", "afraid", "startled")),
        ("peaceful", ("quiet", "gentle", "soft", "calm", "peaceful")),
        ("gently curious", ("noticed", "looked", "wonder", "curious", "peeked")),
        ("warmly magical", ("glow", "sparkle", "magic", "shining")),
        ("joyful", ("happy", "joy", "delighted", "celebrate")),
    ]
    for label, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            return label
    cleaned_fallback = (fallback or "").strip()
    if cleaned_fallback:
        return cleaned_fallback
    return "storybook calm"


def _detect_classic_characters(page_text: str, fallback: str | None = None) -> list[str]:
    names = ["Buddybug", "Verity", "Daphne", "Dolly", "Twinklet", "Whisperwing", "Glowmoth"]
    found = [name for name in names if re.search(rf"\b{re.escape(name)}\b", page_text)]
    if found:
        return found
    return [item.strip() for item in (fallback or "").split(",") if item.strip()]


def _apply_classic_prompt_enhancer(
    payloads: list[dict[str, str | int | None]],
    *,
    adaptation_intensity: str,
    scene_seed_notes: list[ClassicSceneSeedNote],
) -> list[dict[str, str | int | None]]:
    notes_by_index = {note.sceneIndex: note for note in scene_seed_notes}
    enhanced_payloads: list[dict[str, str | int | None]] = []
    for index, payload in enumerate(payloads):
        page_number = int(payload["page_number"])
        note = notes_by_index.get(page_number)
        enhanced = dict(payload)
        page_text = str(payload.get("page_text") or "").strip()
        location = (
            note.setting
            if note and note.setting.strip()
            else _infer_classic_location(page_text, str(payload.get("location") or "").strip())
        )
        mood = (
            note.mood
            if note and note.mood.strip()
            else _infer_classic_mood(page_text, str(payload.get("mood") or "").strip())
        )
        key_visual_action = (
            note.keyVisualAction
            if note and note.keyVisualAction.strip()
            else page_text.split("\n", 1)[0].strip() or str(payload.get("scene_summary") or "").strip()
        ) or "preserve the clearest iconic action from this classic page"
        scene_summary = (
            f"{note.label} in {location} with a {mood} feeling: {key_visual_action}."
            if note is not None
            else f"Classic story scene in {location} with a {mood} feeling: {key_visual_action}."
        )
        characters_present = _detect_classic_characters(
            page_text,
            ", ".join(note.featuredCharacters) if note and note.featuredCharacters else str(payload.get("characters_present") or ""),
        )
        if not characters_present and note and note.featuredCharacters:
            characters_present = note.featuredCharacters
        if not characters_present:
            characters_present = (
                note.featuredCharacters
                if note and note.featuredCharacters
                else [item.strip() for item in str(payload.get("characters_present") or "").split(",") if item.strip()]
            )
        enhanced["location"] = location
        enhanced["mood"] = mood
        enhanced["scene_summary"] = scene_summary
        enhanced["characters_present"] = ", ".join(characters_present)
        enhanced["illustration_prompt"] = build_classic_illustration_prompt(
            page_number=page_number,
            page_text=page_text,
            scene_summary=scene_summary,
            setting=location,
            mood=mood,
            key_visual_action=key_visual_action,
            characters_present=characters_present,
            adaptation_intensity=adaptation_intensity,
            scene_note=note,
            previous_page_text=str(payloads[index - 1].get("page_text") or "").strip() if index > 0 else None,
            next_page_text=str(payloads[index + 1].get("page_text") or "").strip() if index < len(payloads) - 1 else None,
        )
        enhanced_payloads.append(enhanced)
    return enhanced_payloads


def _delete_story_pages_for_draft(session: Session, story_draft_id: int) -> None:
    pages = list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft_id)).all())
    for page in pages:
        illustrations = list(session.exec(select(Illustration).where(Illustration.story_page_id == page.id)).all())
        for illustration in illustrations:
            session.delete(illustration)
        session.delete(page)
    session.commit()


def _rebuild_story_pages_for_draft(
    session: Session,
    *,
    story_draft: StoryDraft,
    adaptation_intensity: str,
    scene_seed_notes_json: str | None,
    min_pages: int,
    max_pages: int,
) -> list[StoryPage]:
    _delete_story_pages_for_draft(session, story_draft.id)
    payloads = generate_story_page_payloads(
        story_draft=story_draft,
        story_idea=None,
        target_page_count=None,
        min_pages=min_pages,
        max_pages=max_pages,
    )
    payloads = _apply_classic_prompt_enhancer(
        payloads,
        adaptation_intensity=adaptation_intensity,
        scene_seed_notes=_parse_scene_seed_notes(scene_seed_notes_json),
    )
    created_pages: list[StoryPage] = []
    for item in payloads:
        page = StoryPage(**item)
        session.add(page)
        created_pages.append(page)
    session.commit()
    for page in created_pages:
        session.refresh(page)
    return created_pages


def create_classic_source(
    session: Session,
    *,
    current_user: User,
    title: str,
    source_text: str,
    source_url: str,
    public_domain_verified: bool,
    source_author: str | None,
    source_origin_notes: str | None,
) -> ClassicSource:
    existing = list(session.exec(select(ClassicSource).where(ClassicSource.title == title.strip())).all())
    normalized_key = _normalized_title_key(title)
    if any(_normalized_title_key(item.title) == normalized_key for item in existing):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A classic source with this title already exists")
    classic_source = ClassicSource(
        title=title.strip(),
        source_text=source_text.strip(),
        source_url=source_url.strip(),
        public_domain_verified=public_domain_verified,
        source_author=source_author.strip() if source_author else None,
        source_origin_notes=source_origin_notes.strip() if source_origin_notes else None,
        import_status="imported",
        created_by_user_id=current_user.id,
    )
    return _persist(session, classic_source)


def update_classic_source(
    session: Session,
    *,
    classic_source: ClassicSource,
    title: str | None = None,
    source_text: str | None = None,
    source_url: str | None = None,
    public_domain_verified: bool | None = None,
    source_author: str | None = None,
    source_origin_notes: str | None = None,
    import_status: str | None = None,
) -> ClassicSource:
    if title is not None and title.strip() and title.strip() != classic_source.title:
        existing = list(session.exec(select(ClassicSource).where(ClassicSource.title == title.strip())).all())
        normalized_key = _normalized_title_key(title)
        if any(item.id != classic_source.id and _normalized_title_key(item.title) == normalized_key for item in existing):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A classic source with this title already exists")
        classic_source.title = title.strip()
    if source_text is not None:
        classic_source.source_text = source_text.strip()
    if source_url is not None:
        classic_source.source_url = source_url.strip()
    if public_domain_verified is not None:
        classic_source.public_domain_verified = public_domain_verified
    if source_author is not None:
        classic_source.source_author = source_author.strip() or None
    if source_origin_notes is not None:
        classic_source.source_origin_notes = source_origin_notes.strip() or None
    if import_status is not None:
        classic_source.import_status = validate_classic_source_status(import_status)
    classic_source.updated_at = utc_now()
    return _persist(session, classic_source)


def archive_classic_source(session: Session, *, classic_source: ClassicSource) -> ClassicSource:
    classic_source.import_status = "archived"
    classic_source.updated_at = utc_now()
    return _persist(session, classic_source)


def create_classic_adaptation(
    session: Session,
    *,
    current_user: User,
    classic_source: ClassicSource,
    age_band: str,
    content_lane_key: str | None,
    language: str,
    adaptation_intensity: str,
    min_pages: int,
    max_pages: int,
) -> ClassicAdaptationDraft:
    if not classic_source.public_domain_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public-domain verification is required before adaptation",
        )
    normalized_language = validate_language_code(language)
    validated_intensity = validate_classic_adaptation_intensity_or_400(adaptation_intensity)
    resolved_lane = validate_content_lane_key(session, age_band=age_band, content_lane_key=content_lane_key).key
    adaptation = adapt_classic_source(
        session,
        classic_source,
        adaptation_intensity=validated_intensity,
        min_scenes=min_pages,
        max_scenes=max_pages,
    )
    project = create_editorial_project(
        session,
        current_user=current_user,
        title=adaptation.adapted_title,
        slug=_build_project_slug(session, adaptation.adapted_title),
        description=f"Classic adaptation of {classic_source.title}",
        age_band=age_band,
        content_lane_key=resolved_lane,
        language=normalized_language,
        status_value="draft",
        assigned_editor_user_id=current_user.id,
        source_type="classic_adaptation",
        notes=f"Source reference: {classic_source.source_url}",
    )
    story_draft = StoryDraft(
        story_idea_id=None,
        project_id=project.id,
        classic_source_id=classic_source.id,
        title=adaptation.adapted_title,
        age_band=age_band,
        language=normalized_language,
        content_lane_key=resolved_lane,
        is_classic=True,
        full_text=adaptation.adapted_text,
        summary=_story_summary(adaptation.adapted_text),
        read_time_minutes=_read_time_minutes(adaptation.adapted_text),
        review_status="draft_pending_review",
        review_notes=adaptation.editor_notes or None,
        approved_text=adaptation.adapted_text,
        generation_source="classic_adaptation",
    )
    story_draft = _persist(session, story_draft)
    story_pages = _rebuild_story_pages_for_draft(
        session,
        story_draft=story_draft,
        adaptation_intensity=validated_intensity,
        scene_seed_notes_json=adaptation.scene_seed_notes_json,
        min_pages=min_pages,
        max_pages=max_pages,
    )
    preview_book, _preview_pages = build_preview_book(session, draft=story_draft)
    classic_draft = ClassicAdaptationDraft(
        classic_source_id=classic_source.id,
        project_id=project.id,
        story_draft_id=story_draft.id,
        preview_book_id=preview_book.id,
        adapted_title=adaptation.adapted_title,
        adapted_text=adaptation.adapted_text,
        adaptation_intensity=validated_intensity,
        adaptation_notes=adaptation.adaptation_notes or None,
        cameo_insertions_summary=adaptation.cameo_insertions_summary or None,
        scene_seed_notes_json=adaptation.scene_seed_notes_json,
        page_scene_data_json=json.dumps(
            [
                {
                    "page_number": page.page_number,
                    "page_text": page.page_text,
                    "scene_summary": page.scene_summary,
                    "location": page.location,
                    "mood": page.mood,
                    "characters_present": page.characters_present,
                    "illustration_prompt": page.illustration_prompt,
                }
                for page in story_pages
            ]
        ),
        validation_status=adaptation.validation_status,
        validation_warnings_json=json.dumps(adaptation.validation_warnings) if adaptation.validation_warnings else None,
        illustration_status="pages_planned",
        review_status="pending",
        editor_notes=adaptation.editor_notes or None,
        created_by_user_id=current_user.id,
    )
    classic_draft = _persist(session, classic_draft)
    classic_source.import_status = "drafted"
    classic_source.updated_at = utc_now()
    session.add(classic_source)
    session.commit()
    session.refresh(classic_source)
    return classic_draft


def update_classic_adaptation(
    session: Session,
    *,
    classic_draft: ClassicAdaptationDraft,
    adapted_title: str | None = None,
    adapted_text: str | None = None,
    adaptation_intensity: str | None = None,
    adaptation_notes: str | None = None,
    cameo_insertions_summary: str | None = None,
    scene_seed_notes_json: str | None = None,
    validation_status: str | None = None,
    validation_warnings_json: str | None = None,
    review_status: str | None = None,
    illustration_status: str | None = None,
    editor_notes: str | None = None,
) -> ClassicAdaptationDraft:
    story_draft = session.get(StoryDraft, classic_draft.story_draft_id) if classic_draft.story_draft_id is not None else None
    rebuild_pages = False
    if adapted_title is not None:
        classic_draft.adapted_title = adapted_title.strip()
        if story_draft is not None:
            story_draft.title = classic_draft.adapted_title
            session.add(story_draft)
    if adapted_text is not None:
        classic_draft.adapted_text = adapted_text.strip()
        rebuild_pages = True
        if story_draft is not None:
            story_draft.full_text = classic_draft.adapted_text
            story_draft.approved_text = classic_draft.adapted_text
            story_draft.summary = _story_summary(classic_draft.adapted_text)
            story_draft.read_time_minutes = _read_time_minutes(classic_draft.adapted_text)
            session.add(story_draft)
    if adaptation_intensity is not None:
        classic_draft.adaptation_intensity = validate_classic_adaptation_intensity_or_400(adaptation_intensity)
        rebuild_pages = True
    if adaptation_notes is not None:
        classic_draft.adaptation_notes = adaptation_notes.strip() or None
    if cameo_insertions_summary is not None:
        classic_draft.cameo_insertions_summary = cameo_insertions_summary.strip() or None
    if scene_seed_notes_json is not None:
        classic_draft.scene_seed_notes_json = scene_seed_notes_json.strip() or None
        rebuild_pages = True
    if validation_status is not None:
        classic_draft.validation_status = validate_classic_validation_status(validation_status)
    if validation_warnings_json is not None:
        classic_draft.validation_warnings_json = validation_warnings_json.strip() or None
    if review_status is not None:
        classic_draft.review_status = validate_classic_draft_review_status(review_status)
    if illustration_status is not None:
        classic_draft.illustration_status = validate_classic_draft_illustration_status(illustration_status)
    if editor_notes is not None:
        classic_draft.editor_notes = editor_notes.strip() or None
        if story_draft is not None:
            story_draft.review_notes = classic_draft.editor_notes
            session.add(story_draft)
    if rebuild_pages and story_draft is not None:
        existing_page_count = len(
            list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft.id)).all())
        ) or 5
        _rebuild_story_pages_for_draft(
            session,
            story_draft=story_draft,
            adaptation_intensity=classic_draft.adaptation_intensity,
            scene_seed_notes_json=classic_draft.scene_seed_notes_json,
            min_pages=existing_page_count,
            max_pages=existing_page_count,
        )
    classic_draft.updated_at = utc_now()
    session.add(classic_draft)
    session.commit()
    session.refresh(classic_draft)
    return classic_draft


def get_classic_draft_bundle(
    session: Session,
    *,
    classic_draft: ClassicAdaptationDraft,
) -> tuple[ClassicSource, StoryDraft | None, list[StoryPage], Book | None, list]:
    classic_source = get_classic_source_or_404(session, classic_draft.classic_source_id)
    story_draft = session.get(StoryDraft, classic_draft.story_draft_id) if classic_draft.story_draft_id is not None else None
    story_pages = (
        list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft.id).order_by(StoryPage.page_number)).all())
        if story_draft is not None
        else []
    )
    preview_book = session.get(Book, classic_draft.preview_book_id) if classic_draft.preview_book_id is not None else None
    preview_pages = (
        list(session.exec(select(BookPage).where(BookPage.book_id == preview_book.id).order_by(BookPage.page_number)).all())
        if preview_book is not None
        else []
    )
    return classic_source, story_draft, story_pages, preview_book, preview_pages


def rebuild_classic_preview_book(session: Session, *, classic_draft: ClassicAdaptationDraft) -> Book:
    if classic_draft.story_draft_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classic adaptation draft is missing a story draft")
    story_draft = session.get(StoryDraft, classic_draft.story_draft_id)
    if story_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    preview_book, _preview_pages = build_preview_book(session, draft=story_draft)
    preview_book.is_classic = True
    preview_book.classic_source_id = classic_draft.classic_source_id
    preview_book.updated_at = utc_now()
    preview_book = _persist(session, preview_book)
    classic_draft.preview_book_id = preview_book.id
    classic_draft.updated_at = utc_now()
    session.add(classic_draft)
    session.commit()
    session.refresh(classic_draft)
    return preview_book


def generate_classic_illustrations(session: Session, *, classic_draft: ClassicAdaptationDraft) -> dict[str, object]:
    if classic_draft.story_draft_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classic adaptation draft is missing a story draft")
    story_pages = list(
        session.exec(
            select(StoryPage).where(StoryPage.story_draft_id == classic_draft.story_draft_id).order_by(StoryPage.page_number)
        ).all()
    )
    if not story_pages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No story pages available for illustration generation")

    illustration_ids: list[int] = []
    for page in story_pages:
        illustration = generate_illustration_asset(
            session,
            story_page=page,
            provider=None,
            generation_notes="Classic adaptation illustration",
        )
        evaluate_illustration_quality(session, illustration_id=illustration.id)
        illustration_ids.append(illustration.id)
    classic_draft.illustration_status = "illustrated"
    classic_draft.updated_at = utc_now()
    session.add(classic_draft)
    classic_source = get_classic_source_or_404(session, classic_draft.classic_source_id)
    classic_source.import_status = "illustrated"
    classic_source.updated_at = utc_now()
    session.add(classic_source)
    session.commit()
    rebuild_classic_preview_book(session, classic_draft=classic_draft)
    return {
        "classic_adaptation_draft_id": classic_draft.id,
        "story_draft_id": classic_draft.story_draft_id,
        "generated_count": len(illustration_ids),
        "illustration_ids": illustration_ids,
        "page_ids": [page.id for page in story_pages],
        "provider": "default",
    }


def approve_classic_adaptation(
    session: Session,
    *,
    classic_draft: ClassicAdaptationDraft,
    editor_notes: str | None = None,
) -> ClassicAdaptationDraft:
    if classic_draft.validation_status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classic adaptation draft failed validation and must be fixed before approval",
        )
    classic_draft.review_status = "approved"
    if editor_notes is not None:
        classic_draft.editor_notes = editor_notes.strip() or None
    classic_draft.updated_at = utc_now()
    session.add(classic_draft)
    if classic_draft.story_draft_id is not None:
        story_draft = session.get(StoryDraft, classic_draft.story_draft_id)
        if story_draft is not None:
            story_draft.review_status = "approved_for_illustration"
            if classic_draft.editor_notes is not None:
                story_draft.review_notes = classic_draft.editor_notes
            story_draft.updated_at = utc_now()
            session.add(story_draft)
    classic_source = get_classic_source_or_404(session, classic_draft.classic_source_id)
    classic_source.import_status = "approved"
    classic_source.updated_at = utc_now()
    session.add(classic_source)
    session.commit()
    session.refresh(classic_draft)
    return classic_draft


def archive_classic_adaptation(session: Session, *, classic_draft: ClassicAdaptationDraft) -> ClassicAdaptationDraft:
    classic_draft.review_status = "archived"
    classic_draft.illustration_status = "archived"
    classic_draft.updated_at = utc_now()
    return _persist(session, classic_draft)


def publish_classic_adaptation(session: Session, *, classic_draft: ClassicAdaptationDraft) -> Book:
    if classic_draft.review_status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classic adaptation draft must be approved before publish")
    if classic_draft.story_draft_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classic adaptation draft is missing a story draft")
    story_draft = session.get(StoryDraft, classic_draft.story_draft_id)
    if story_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    story_pages = list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft.id).order_by(StoryPage.page_number)).all())
    validate_story_pages_ready_for_release(session, story_pages=story_pages)
    preview_book = rebuild_classic_preview_book(session, classic_draft=classic_draft)
    existing_published = list(
        session.exec(select(Book).where(Book.story_draft_id == story_draft.id, Book.id != preview_book.id, Book.published.is_(True))).all()
    )
    for existing in existing_published:
        existing.published = False
        existing.publication_status = "archived"
        existing.updated_at = utc_now()
        session.add(existing)
    preview_book.is_classic = True
    preview_book.classic_source_id = classic_draft.classic_source_id
    preview_book.published = True
    preview_book.publication_status = "published"
    preview_book.updated_at = utc_now()
    session.add(preview_book)
    classic_draft.illustration_status = "published"
    classic_draft.updated_at = utc_now()
    session.add(classic_draft)
    classic_source = get_classic_source_or_404(session, classic_draft.classic_source_id)
    classic_source.import_status = "published"
    classic_source.updated_at = utc_now()
    session.add(classic_source)
    session.commit()
    session.refresh(preview_book)
    auto_generate_default_narration_for_book(session, book=preview_book, replace_existing=False)
    return preview_book
