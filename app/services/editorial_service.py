from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Book, BookPage, EditorialAsset, EditorialProject, StoryDraft, StoryPage, User
from app.services.book_builder import build_cover_page, determine_layout_type
from app.services.child_profile_service import SUPPORTED_CHILD_AGE_BANDS
from app.services.content_version_service import snapshot_story_draft, snapshot_story_page
from app.services.content_lane_service import validate_content_lane_key
from app.services.i18n_service import validate_language_code
from app.services.quality_service import run_story_draft_quality_checks, run_story_pages_quality_checks
from app.services.review_service import utc_now, validate_review_status

EDITORIAL_PROJECT_STATUSES = {
    "draft",
    "in_review",
    "ready_for_preview",
    "ready_for_publish",
    "published",
    "archived",
}
EDITORIAL_SOURCE_TYPES = {"ai_generated", "manual", "mixed"}
EDITORIAL_ASSET_TYPES = {"cover_image", "page_image", "manuscript_file", "reference_image"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_editorial_project_status(status_value: str) -> str:
    if status_value not in EDITORIAL_PROJECT_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid editorial project status")
    return status_value


def validate_editorial_source_type(source_type: str) -> str:
    if source_type not in EDITORIAL_SOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid editorial source type")
    return source_type


def validate_editorial_asset_type(asset_type: str) -> str:
    if asset_type not in EDITORIAL_ASSET_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid editorial asset type")
    return asset_type


def validate_editorial_age_band(age_band: str) -> str:
    if age_band not in SUPPORTED_CHILD_AGE_BANDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported age band")
    return age_band


def _resolve_lane_key(session: Session, *, age_band: str, content_lane_key: str | None) -> str | None:
    if content_lane_key is None:
        return None
    return validate_content_lane_key(session, age_band=age_band, content_lane_key=content_lane_key).key


def get_editorial_project_or_404(session: Session, project_id: int) -> EditorialProject:
    project = session.get(EditorialProject, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editorial project not found")
    return project


def get_editorial_asset_or_404(session: Session, asset_id: int) -> EditorialAsset:
    asset = session.get(EditorialAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editorial asset not found")
    return asset


def get_editorial_draft_or_404(session: Session, draft_id: int) -> StoryDraft:
    draft = session.get(StoryDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    return draft


def get_editorial_story_page_or_404(session: Session, page_id: int) -> StoryPage:
    page = session.get(StoryPage, page_id)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story page not found")
    return page


def list_editorial_projects(
    session: Session,
    *,
    status_value: str | None,
    source_type: str | None,
    language: str | None,
    limit: int,
) -> list[EditorialProject]:
    statement = select(EditorialProject).order_by(EditorialProject.updated_at.desc()).limit(limit)
    if status_value is not None:
        validate_editorial_project_status(status_value)
        statement = statement.where(EditorialProject.status == status_value)
    if source_type is not None:
        validate_editorial_source_type(source_type)
        statement = statement.where(EditorialProject.source_type == source_type)
    if language is not None:
        statement = statement.where(EditorialProject.language == validate_language_code(language))
    return list(session.exec(statement).all())


def create_editorial_project(
    session: Session,
    *,
    current_user: User,
    title: str,
    slug: str,
    description: str | None,
    age_band: str,
    content_lane_key: str | None,
    language: str,
    status_value: str,
    assigned_editor_user_id: int | None,
    source_type: str,
    notes: str | None,
) -> EditorialProject:
    existing = session.exec(select(EditorialProject).where(EditorialProject.slug == slug)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Editorial project slug already exists")
    project = EditorialProject(
        title=title,
        slug=slug,
        description=description,
        age_band=validate_editorial_age_band(age_band),
        content_lane_key=_resolve_lane_key(session, age_band=age_band, content_lane_key=content_lane_key),
        language=validate_language_code(language),
        status=validate_editorial_project_status(status_value),
        created_by_user_id=current_user.id,
        assigned_editor_user_id=assigned_editor_user_id,
        source_type=validate_editorial_source_type(source_type),
        notes=notes,
    )
    return _persist(session, project)


def update_editorial_project(
    session: Session,
    *,
    project: EditorialProject,
    title: str | None = None,
    slug: str | None = None,
    description: str | None = None,
    age_band: str | None = None,
    content_lane_key: str | None = None,
    language: str | None = None,
    status_value: str | None = None,
    assigned_editor_user_id: int | None = None,
    source_type: str | None = None,
    notes: str | None = None,
) -> EditorialProject:
    resolved_age_band = validate_editorial_age_band(age_band or project.age_band)
    if title is not None:
        project.title = title
    if slug is not None and slug != project.slug:
        existing = session.exec(select(EditorialProject).where(EditorialProject.slug == slug)).first()
        if existing is not None and existing.id != project.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Editorial project slug already exists")
        project.slug = slug
    if description is not None:
        project.description = description
    project.age_band = resolved_age_band
    if content_lane_key is not None:
        project.content_lane_key = _resolve_lane_key(session, age_band=resolved_age_band, content_lane_key=content_lane_key)
    elif age_band is not None and project.content_lane_key is not None:
        project.content_lane_key = _resolve_lane_key(session, age_band=resolved_age_band, content_lane_key=project.content_lane_key)
    if language is not None:
        project.language = validate_language_code(language)
    if status_value is not None:
        project.status = validate_editorial_project_status(status_value)
    if assigned_editor_user_id is not None:
        project.assigned_editor_user_id = assigned_editor_user_id
    if source_type is not None:
        project.source_type = validate_editorial_source_type(source_type)
    if notes is not None:
        project.notes = notes
    project.updated_at = utc_now()
    return _persist(session, project)


def archive_editorial_project(session: Session, *, project: EditorialProject) -> EditorialProject:
    project.status = "archived"
    project.updated_at = utc_now()
    return _persist(session, project)


def list_editorial_assets(session: Session, *, project_id: int) -> list[EditorialAsset]:
    return list(
        session.exec(
            select(EditorialAsset)
            .where(EditorialAsset.project_id == project_id)
            .order_by(EditorialAsset.asset_type.asc(), EditorialAsset.page_number.asc(), EditorialAsset.created_at.asc())
        ).all()
    )


def _deactivate_conflicting_assets(
    session: Session,
    *,
    project_id: int,
    asset_type: str,
    page_number: int | None,
    keep_asset_id: int | None = None,
) -> None:
    statement = select(EditorialAsset).where(
        EditorialAsset.project_id == project_id,
        EditorialAsset.asset_type == asset_type,
    )
    if page_number is None:
        statement = statement.where(EditorialAsset.page_number == None)  # noqa: E711
    else:
        statement = statement.where(EditorialAsset.page_number == page_number)
    existing_assets = list(session.exec(statement).all())
    changed = False
    for existing in existing_assets:
        if keep_asset_id is not None and existing.id == keep_asset_id:
            continue
        if existing.is_active:
            existing.is_active = False
            existing.updated_at = utc_now()
            session.add(existing)
            changed = True
    if changed:
        session.commit()


def create_editorial_asset(
    session: Session,
    *,
    current_user: User,
    project: EditorialProject,
    asset_type: str,
    file_url: str,
    language: str | None,
    page_number: int | None,
    is_active: bool,
) -> EditorialAsset:
    normalized_type = validate_editorial_asset_type(asset_type)
    if language is not None:
        language = validate_language_code(language)
    if normalized_type == "cover_image" and page_number is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cover assets cannot target a page number")
    if normalized_type != "page_image":
        page_number = None if normalized_type != "page_image" else page_number
    asset = EditorialAsset(
        project_id=project.id,
        asset_type=normalized_type,
        file_url=file_url,
        language=language,
        page_number=page_number,
        is_active=is_active,
        created_by_user_id=current_user.id,
    )
    asset = _persist(session, asset)
    if is_active:
        _deactivate_conflicting_assets(
            session,
            project_id=project.id,
            asset_type=asset.asset_type,
            page_number=asset.page_number,
            keep_asset_id=asset.id,
        )
        session.refresh(asset)
    return asset


def update_editorial_asset(
    session: Session,
    *,
    asset: EditorialAsset,
    asset_type: str | None = None,
    file_url: str | None = None,
    language: str | None = None,
    page_number: int | None = None,
    is_active: bool | None = None,
) -> EditorialAsset:
    if asset_type is not None:
        asset.asset_type = validate_editorial_asset_type(asset_type)
    if file_url is not None:
        asset.file_url = file_url
    if language is not None:
        asset.language = validate_language_code(language)
    if page_number is not None or (asset.asset_type != "page_image"):
        asset.page_number = page_number if asset.asset_type == "page_image" else None
    if is_active is not None:
        asset.is_active = is_active
    asset.updated_at = utc_now()
    asset = _persist(session, asset)
    if asset.is_active:
        _deactivate_conflicting_assets(
            session,
            project_id=asset.project_id,
            asset_type=asset.asset_type,
            page_number=asset.page_number,
            keep_asset_id=asset.id,
        )
        session.refresh(asset)
    return asset


def delete_editorial_asset(session: Session, *, asset: EditorialAsset) -> None:
    session.delete(asset)
    session.commit()


def get_project_draft(session: Session, *, project_id: int) -> StoryDraft | None:
    return session.exec(select(StoryDraft).where(StoryDraft.project_id == project_id).order_by(StoryDraft.updated_at.desc())).first()


def list_story_pages_for_draft(session: Session, *, story_draft_id: int) -> list[StoryPage]:
    return list(
        session.exec(
            select(StoryPage).where(StoryPage.story_draft_id == story_draft_id).order_by(StoryPage.page_number.asc())
        ).all()
    )


def get_preview_book_for_draft(session: Session, *, story_draft_id: int) -> Book | None:
    return session.exec(
        select(Book)
        .where(Book.story_draft_id == story_draft_id, Book.published.is_(False))
        .order_by(Book.updated_at.desc())
    ).first()


def create_manual_story_draft(
    session: Session,
    *,
    title: str,
    full_text: str,
    summary: str,
    age_band: str,
    content_lane_key: str | None,
    language: str,
    review_status: str,
    project_id: int | None,
    read_time_minutes: int | None,
) -> StoryDraft:
    project = get_editorial_project_or_404(session, project_id) if project_id is not None else None
    validated_age_band = validate_editorial_age_band(age_band if project is None else project.age_band)
    draft = StoryDraft(
        story_idea_id=None,
        project_id=project.id if project is not None else None,
        title=title,
        age_band=validated_age_band,
        language=validate_language_code(language if project is None else project.language),
        content_lane_key=_resolve_lane_key(
            session,
            age_band=validated_age_band,
            content_lane_key=content_lane_key if content_lane_key is not None else (project.content_lane_key if project is not None else None),
        ),
        full_text=full_text,
        summary=summary,
        read_time_minutes=read_time_minutes or 5,
        review_status=validate_review_status(review_status),
        generation_source="manual",
    )
    return _persist(session, draft)


def update_manual_story_draft(
    session: Session,
    *,
    draft: StoryDraft,
    created_by_user_id: int | None = None,
    title: str | None = None,
    full_text: str | None = None,
    summary: str | None = None,
    age_band: str | None = None,
    content_lane_key: str | None = None,
    language: str | None = None,
    review_status: str | None = None,
    project_id: int | None = None,
    read_time_minutes: int | None = None,
    review_notes: str | None = None,
    approved_text: str | None = None,
) -> StoryDraft:
    project = get_editorial_project_or_404(session, project_id) if project_id is not None else None
    resolved_age_band = validate_editorial_age_band(age_band or draft.age_band)
    resolved_content_lane_key = (
        _resolve_lane_key(session, age_band=resolved_age_band, content_lane_key=content_lane_key)
        if content_lane_key is not None
        else draft.content_lane_key
    )
    resolved_language = validate_language_code(language) if language is not None else draft.language
    resolved_review_status = validate_review_status(review_status) if review_status is not None else draft.review_status
    changed = False
    if title is not None and title != draft.title:
        changed = True
    if full_text is not None and full_text != draft.full_text:
        changed = True
    if summary is not None and summary != draft.summary:
        changed = True
    if project is not None and project.id != draft.project_id:
        changed = True
    if resolved_age_band != draft.age_band:
        changed = True
    if resolved_content_lane_key != draft.content_lane_key:
        changed = True
    if resolved_language != draft.language:
        changed = True
    if resolved_review_status != draft.review_status:
        changed = True
    if read_time_minutes is not None and read_time_minutes != draft.read_time_minutes:
        changed = True
    if review_notes is not None and review_notes != draft.review_notes:
        changed = True
    if approved_text is not None and approved_text != draft.approved_text:
        changed = True
    if changed:
        snapshot_story_draft(session, story_draft=draft, created_by_user_id=created_by_user_id)
    if title is not None:
        draft.title = title
    if full_text is not None:
        draft.full_text = full_text
    if summary is not None:
        draft.summary = summary
    if project is not None:
        draft.project_id = project.id
    draft.age_band = resolved_age_band
    draft.content_lane_key = resolved_content_lane_key
    draft.language = resolved_language
    draft.review_status = resolved_review_status
    if read_time_minutes is not None:
        draft.read_time_minutes = read_time_minutes
    if review_notes is not None:
        draft.review_notes = review_notes
    if approved_text is not None:
        draft.approved_text = approved_text
    draft.updated_at = utc_now()
    return _persist(session, draft)


def create_manual_story_page(
    session: Session,
    *,
    story_draft_id: int,
    page_number: int,
    page_text: str,
    scene_summary: str,
    location: str,
    mood: str,
    characters_present: str,
    illustration_prompt: str | None,
    image_url: str | None,
) -> StoryPage:
    get_editorial_draft_or_404(session, story_draft_id)
    existing = session.exec(
        select(StoryPage).where(StoryPage.story_draft_id == story_draft_id, StoryPage.page_number == page_number)
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A page already exists for that page number")
    page = StoryPage(
        story_draft_id=story_draft_id,
        page_number=page_number,
        page_text=page_text,
        scene_summary=scene_summary,
        location=location,
        mood=mood,
        characters_present=characters_present,
        illustration_prompt=illustration_prompt or "",
        image_status="prompt_ready",
        image_url=image_url,
    )
    return _persist(session, page)


def update_manual_story_page(
    session: Session,
    *,
    page: StoryPage,
    created_by_user_id: int | None = None,
    page_number: int | None = None,
    page_text: str | None = None,
    scene_summary: str | None = None,
    location: str | None = None,
    mood: str | None = None,
    characters_present: str | None = None,
    illustration_prompt: str | None = None,
    image_url: str | None = None,
) -> StoryPage:
    if page_number is not None and page_number != page.page_number:
        existing = session.exec(
            select(StoryPage).where(StoryPage.story_draft_id == page.story_draft_id, StoryPage.page_number == page_number)
        ).first()
        if existing is not None and existing.id != page.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A page already exists for that page number")
    changed = False
    if page_number is not None and page_number != page.page_number:
        changed = True
    if page_text is not None and page_text != page.page_text:
        changed = True
    if scene_summary is not None and scene_summary != page.scene_summary:
        changed = True
    if location is not None and location != page.location:
        changed = True
    if mood is not None and mood != page.mood:
        changed = True
    if characters_present is not None and characters_present != page.characters_present:
        changed = True
    if illustration_prompt is not None and illustration_prompt != page.illustration_prompt:
        changed = True
    if image_url is not None and image_url != page.image_url:
        changed = True
    if changed:
        snapshot_story_page(session, story_page=page, created_by_user_id=created_by_user_id)
    if page_number is not None and page_number != page.page_number:
        page.page_number = page_number
    if page_text is not None:
        page.page_text = page_text
    if scene_summary is not None:
        page.scene_summary = scene_summary
    if location is not None:
        page.location = location
    if mood is not None:
        page.mood = mood
    if characters_present is not None:
        page.characters_present = characters_present
    if illustration_prompt is not None:
        page.illustration_prompt = illustration_prompt
    if image_url is not None:
        page.image_url = image_url
    page.updated_at = utc_now()
    return _persist(session, page)


def _active_asset_map(session: Session, *, project_id: int) -> tuple[str | None, dict[int, str]]:
    assets = list(
        session.exec(
            select(EditorialAsset).where(
                EditorialAsset.project_id == project_id,
                EditorialAsset.is_active.is_(True),
            )
        ).all()
    )
    cover_image_url = next((asset.file_url for asset in assets if asset.asset_type == "cover_image"), None)
    page_images = {
        asset.page_number: asset.file_url
        for asset in assets
        if asset.asset_type == "page_image" and asset.page_number is not None
    }
    return cover_image_url, page_images


def _delete_book_pages(session: Session, *, book_id: int) -> None:
    for page in list(session.exec(select(BookPage).where(BookPage.book_id == book_id)).all()):
        session.delete(page)
    session.commit()


def build_preview_book(session: Session, *, draft: StoryDraft) -> tuple[Book, list[BookPage]]:
    story_pages = list_story_pages_for_draft(session, story_draft_id=draft.id)
    if not story_pages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Story pages must exist before building preview")

    preview_book = get_preview_book_for_draft(session, story_draft_id=draft.id)
    if preview_book is None:
        preview_book = Book(
            story_draft_id=draft.id,
            title=draft.title,
            age_band=draft.age_band,
            content_lane_key=draft.content_lane_key,
            language=draft.language,
            published=False,
            publication_status="ready",
            audio_available=False,
        )
        preview_book = _persist(session, preview_book)
    else:
        _delete_book_pages(session, book_id=preview_book.id)
        preview_book.title = draft.title
        preview_book.age_band = draft.age_band
        preview_book.content_lane_key = draft.content_lane_key
        preview_book.language = draft.language
        preview_book.published = False
        preview_book.publication_status = "ready"

    cover_override = None
    page_image_overrides: dict[int, str] = {}
    if draft.project_id is not None:
        cover_override, page_image_overrides = _active_asset_map(session, project_id=draft.project_id)

    preview_book.cover_image_url = cover_override or story_pages[0].image_url
    preview_book.updated_at = utc_now()
    preview_book = _persist(session, preview_book)

    pages: list[BookPage] = [build_cover_page(preview_book.id, preview_book.title, preview_book.cover_image_url)]
    for story_page in story_pages:
        resolved_image_url = page_image_overrides.get(story_page.page_number, story_page.image_url)
        pages.append(
            BookPage(
                book_id=preview_book.id,
                source_story_page_id=story_page.id,
                page_number=story_page.page_number,
                text_content=story_page.page_text,
                image_url=resolved_image_url,
                layout_type=determine_layout_type(story_page.page_text, resolved_image_url),
            )
        )
    for page in pages:
        session.add(page)
    session.commit()
    for page in pages:
        session.refresh(page)
    return preview_book, pages


def mark_project_ready_for_publish(session: Session, *, project: EditorialProject) -> EditorialProject:
    draft = get_project_draft(session, project_id=project.id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A project draft must exist before publishing")
    story_pages = list_story_pages_for_draft(session, story_draft_id=draft.id)
    if not story_pages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Story pages must exist before publishing")
    project.status = "ready_for_publish"
    project.updated_at = utc_now()
    return _persist(session, project)


def publish_project(session: Session, *, project: EditorialProject) -> tuple[EditorialProject, Book]:
    if project.status != "ready_for_publish":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project must be ready_for_publish before publishing")
    draft = get_project_draft(session, project_id=project.id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project draft is missing")
    book, _pages = build_preview_book(session, draft=draft)
    existing_published = list(
        session.exec(select(Book).where(Book.story_draft_id == draft.id, Book.id != book.id, Book.published.is_(True))).all()
    )
    for existing in existing_published:
        existing.published = False
        existing.publication_status = "archived"
        existing.updated_at = utc_now()
        session.add(existing)
    book.published = True
    book.publication_status = "published"
    book.updated_at = utc_now()
    session.add(book)
    project.status = "published"
    project.updated_at = utc_now()
    session.add(project)
    session.commit()
    session.refresh(project)
    session.refresh(book)
    return project, book


def get_project_draft_bundle(session: Session, *, project_id: int) -> tuple[StoryDraft | None, list[StoryPage], Book | None]:
    draft = get_project_draft(session, project_id=project_id)
    if draft is None:
        return None, [], None
    pages = list_story_pages_for_draft(session, story_draft_id=draft.id)
    preview_book = get_preview_book_for_draft(session, story_draft_id=draft.id)
    return draft, pages, preview_book


def run_editorial_quality_checks(session: Session, *, story_draft_id: int):
    draft_checks = run_story_draft_quality_checks(session, story_draft_id=story_draft_id)
    page_checks = run_story_pages_quality_checks(session, story_draft_id=story_draft_id)
    return draft_checks, page_checks
