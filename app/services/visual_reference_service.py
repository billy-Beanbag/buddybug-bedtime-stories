from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, Character, ContentLane, EditorialProject, StoryDraft, StoryPage, VisualReferenceAsset
from app.models.user import utc_now
from app.services.i18n_service import validate_language_code

REFERENCE_TYPES = {"character_sheet", "style_reference", "cover_reference", "scene_reference"}
TARGET_TYPES = {"character", "content_lane", "editorial_project", "book", "story_draft"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_reference_type(reference_type: str) -> str:
    if reference_type not in REFERENCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid visual reference type")
    return reference_type


def validate_target_type(target_type: str) -> str:
    if target_type not in TARGET_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid visual reference target type")
    return target_type


def _normalize_language(language: str | None) -> str | None:
    if language is None:
        return None
    stripped = language.strip()
    if not stripped:
        return None
    return validate_language_code(stripped)


def _validate_target_pair(target_type: str | None, target_id: int | None) -> tuple[str | None, int | None]:
    if target_type is None and target_id is None:
        return None, None
    if target_type is None or target_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_type and target_id must be provided together",
        )
    return validate_target_type(target_type), target_id


def _validate_target_exists(session: Session, *, target_type: str | None, target_id: int | None) -> None:
    if target_type is None or target_id is None:
        return
    model_map = {
        "character": Character,
        "content_lane": ContentLane,
        "editorial_project": EditorialProject,
        "book": Book,
        "story_draft": StoryDraft,
    }
    model_cls = model_map[target_type]
    if session.get(model_cls, target_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual reference target not found")


def get_visual_reference_asset_or_404(session: Session, *, asset_id: int) -> VisualReferenceAsset:
    asset = session.get(VisualReferenceAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual reference asset not found")
    return asset


def list_visual_reference_assets(
    session: Session,
    *,
    reference_type: str | None,
    target_type: str | None,
    target_id: int | None,
    language: str | None,
    is_active: bool | None,
    limit: int,
) -> list[VisualReferenceAsset]:
    validated_target_type, validated_target_id = _validate_target_pair(target_type, target_id)
    normalized_language = _normalize_language(language)
    statement = select(VisualReferenceAsset).order_by(VisualReferenceAsset.updated_at.desc()).limit(limit)
    if reference_type is not None:
        statement = statement.where(VisualReferenceAsset.reference_type == validate_reference_type(reference_type))
    if validated_target_type is not None and validated_target_id is not None:
        statement = statement.where(
            VisualReferenceAsset.target_type == validated_target_type,
            VisualReferenceAsset.target_id == validated_target_id,
        )
    if normalized_language is not None:
        statement = statement.where(VisualReferenceAsset.language == normalized_language)
    if is_active is not None:
        statement = statement.where(VisualReferenceAsset.is_active == is_active)
    return list(session.exec(statement).all())


def get_visual_references_by_target(
    session: Session,
    *,
    target_type: str,
    target_id: int,
    include_inactive: bool = False,
) -> list[VisualReferenceAsset]:
    normalized_target_type, normalized_target_id = _validate_target_pair(target_type, target_id)
    _validate_target_exists(session, target_type=normalized_target_type, target_id=normalized_target_id)
    statement = (
        select(VisualReferenceAsset)
        .where(
            VisualReferenceAsset.target_type == normalized_target_type,
            VisualReferenceAsset.target_id == normalized_target_id,
        )
        .order_by(VisualReferenceAsset.reference_type.asc(), VisualReferenceAsset.updated_at.desc())
    )
    if not include_inactive:
        statement = statement.where(VisualReferenceAsset.is_active.is_(True))
    return list(session.exec(statement).all())


def _get_content_lane_by_key(session: Session, *, lane_key: str | None) -> ContentLane | None:
    if lane_key is None:
        return None
    return session.exec(select(ContentLane).where(ContentLane.key == lane_key)).first()


def _get_character_by_name(session: Session, *, name: str) -> Character | None:
    stripped = name.strip()
    if not stripped:
        return None
    return session.exec(select(Character).where(Character.name == stripped)).first()


def _split_names(raw_names: str | None) -> list[str]:
    if not raw_names:
        return []
    return [name.strip() for name in raw_names.split(",") if name.strip()]


def _global_visual_references(session: Session, *, include_inactive: bool) -> list[VisualReferenceAsset]:
    statement = select(VisualReferenceAsset).where(
        VisualReferenceAsset.target_type.is_(None),
        VisualReferenceAsset.target_id.is_(None),
    ).order_by(VisualReferenceAsset.reference_type.asc(), VisualReferenceAsset.updated_at.desc())
    if not include_inactive:
        statement = statement.where(VisualReferenceAsset.is_active.is_(True))
    return list(session.exec(statement).all())


def list_recommended_visual_references_for_story_draft(
    session: Session,
    *,
    story_draft_id: int,
    include_inactive: bool = False,
) -> list[VisualReferenceAsset]:
    draft = session.get(StoryDraft, story_draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")

    collected: list[VisualReferenceAsset] = []
    seen_ids: set[int] = set()

    def append_assets(items: list[VisualReferenceAsset]) -> None:
        for item in items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                collected.append(item)

    append_assets(
        get_visual_references_by_target(
            session,
            target_type="story_draft",
            target_id=draft.id,
            include_inactive=include_inactive,
        )
    )
    if draft.project_id is not None:
        append_assets(
            get_visual_references_by_target(
                session,
                target_type="editorial_project",
                target_id=draft.project_id,
                include_inactive=include_inactive,
            )
        )
    lane = _get_content_lane_by_key(session, lane_key=draft.content_lane_key)
    if lane is not None:
        append_assets(
            get_visual_references_by_target(
                session,
                target_type="content_lane",
                target_id=lane.id,
                include_inactive=include_inactive,
            )
        )
    append_assets(_global_visual_references(session, include_inactive=include_inactive))
    return collected


def list_recommended_visual_references_for_story_page(
    session: Session,
    *,
    story_page_id: int,
    include_inactive: bool = False,
) -> list[VisualReferenceAsset]:
    story_page = session.get(StoryPage, story_page_id)
    if story_page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story page not found")

    collected: list[VisualReferenceAsset] = []
    seen_ids: set[int] = set()

    def append_assets(items: list[VisualReferenceAsset]) -> None:
        for item in items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                collected.append(item)

    append_assets(
        list_recommended_visual_references_for_story_draft(
            session,
            story_draft_id=story_page.story_draft_id,
            include_inactive=include_inactive,
        )
    )

    for character_name in _split_names(story_page.characters_present):
        character = _get_character_by_name(session, name=character_name)
        if character is None:
            continue
        append_assets(
            get_visual_references_by_target(
                session,
                target_type="character",
                target_id=character.id,
                include_inactive=include_inactive,
            )
        )

    return collected


def create_visual_reference_asset(
    session: Session,
    *,
    name: str,
    reference_type: str,
    target_type: str | None,
    target_id: int | None,
    image_url: str,
    prompt_notes: str | None,
    language: str | None,
    is_active: bool,
    created_by_user_id: int | None,
) -> VisualReferenceAsset:
    normalized_target_type, normalized_target_id = _validate_target_pair(target_type, target_id)
    _validate_target_exists(session, target_type=normalized_target_type, target_id=normalized_target_id)
    asset = VisualReferenceAsset(
        name=name.strip(),
        reference_type=validate_reference_type(reference_type),
        target_type=normalized_target_type,
        target_id=normalized_target_id,
        image_url=image_url.strip(),
        prompt_notes=prompt_notes.strip() if prompt_notes is not None and prompt_notes.strip() else None,
        language=_normalize_language(language),
        is_active=is_active,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, asset)


def update_visual_reference_asset(
    session: Session,
    *,
    asset: VisualReferenceAsset,
    name: str | None = None,
    reference_type: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    image_url: str | None = None,
    prompt_notes: str | None = None,
    language: str | None = None,
    is_active: bool | None = None,
    target_type_provided: bool = False,
    target_id_provided: bool = False,
    prompt_notes_provided: bool = False,
    language_provided: bool = False,
) -> VisualReferenceAsset:
    if name is not None:
        asset.name = name.strip()
    if reference_type is not None:
        asset.reference_type = validate_reference_type(reference_type)

    next_target_type = asset.target_type
    next_target_id = asset.target_id
    if target_type_provided:
        next_target_type = target_type
    if target_id_provided:
        next_target_id = target_id
    normalized_target_type, normalized_target_id = _validate_target_pair(next_target_type, next_target_id)
    _validate_target_exists(session, target_type=normalized_target_type, target_id=normalized_target_id)
    asset.target_type = normalized_target_type
    asset.target_id = normalized_target_id

    if image_url is not None:
        asset.image_url = image_url.strip()
    if prompt_notes_provided:
        asset.prompt_notes = prompt_notes.strip() if prompt_notes is not None and prompt_notes.strip() else None
    if language_provided:
        asset.language = _normalize_language(language)
    if is_active is not None:
        asset.is_active = is_active
    asset.updated_at = utc_now()
    return _persist(session, asset)


def delete_visual_reference_asset(session: Session, *, asset: VisualReferenceAsset) -> None:
    session.delete(asset)
    session.commit()
