from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.book_schema import BookPageRead, BookRead
from app.schemas.classic_schema import (
    ClassicAdaptationCreateRequest,
    ClassicAdaptationDraftRead,
    ClassicAdaptationUpdate,
    ClassicApproveRequest,
    ClassicDraftBundleResponse,
    ClassicIllustrationGenerationResponse,
    ClassicPublishResponse,
    ClassicSourceCreate,
    ClassicSourceRead,
    ClassicSourceUpdate,
)
from app.schemas.story_schema import StoryDraftRead, StoryPageRead
from app.services.classics_service import (
    approve_classic_adaptation,
    archive_classic_adaptation,
    archive_classic_source,
    create_classic_adaptation,
    create_classic_source,
    generate_classic_illustrations,
    get_classic_adaptation_or_404,
    get_classic_draft_bundle,
    get_classic_source_or_404,
    list_classic_adaptations,
    list_classic_sources,
    publish_classic_adaptation,
    rebuild_classic_preview_book,
    update_classic_adaptation,
    update_classic_source,
)
from app.utils.dependencies import get_current_editor_user

router = APIRouter(
    prefix="/classics",
    tags=["classics"],
    dependencies=[Depends(get_current_editor_user)],
)


@router.get("/sources", response_model=list[ClassicSourceRead], summary="List internal classic sources")
def get_classic_sources(
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[ClassicSourceRead]:
    return list_classic_sources(session, status_value=status_value, limit=limit)


@router.post("/sources", response_model=ClassicSourceRead, status_code=status.HTTP_201_CREATED, summary="Create classic source")
def post_classic_source(
    payload: ClassicSourceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ClassicSourceRead:
    return create_classic_source(
        session,
        current_user=current_user,
        title=payload.title,
        source_text=payload.source_text,
        source_url=payload.source_url,
        public_domain_verified=payload.public_domain_verified,
        source_author=payload.source_author,
        source_origin_notes=payload.source_origin_notes,
    )


@router.get("/sources/{classic_source_id}", response_model=ClassicSourceRead, summary="Get classic source")
def get_classic_source(classic_source_id: int, session: Session = Depends(get_session)) -> ClassicSourceRead:
    return get_classic_source_or_404(session, classic_source_id)


@router.patch("/sources/{classic_source_id}", response_model=ClassicSourceRead, summary="Update classic source")
def patch_classic_source(
    classic_source_id: int,
    payload: ClassicSourceUpdate,
    session: Session = Depends(get_session),
) -> ClassicSourceRead:
    classic_source = get_classic_source_or_404(session, classic_source_id)
    return update_classic_source(
        session,
        classic_source=classic_source,
        title=payload.title,
        source_text=payload.source_text,
        source_url=payload.source_url,
        public_domain_verified=payload.public_domain_verified,
        source_author=payload.source_author,
        source_origin_notes=payload.source_origin_notes,
        import_status=payload.import_status,
    )


@router.post("/sources/{classic_source_id}/archive", response_model=ClassicSourceRead, summary="Archive classic source")
def post_archive_classic_source(
    classic_source_id: int,
    session: Session = Depends(get_session),
) -> ClassicSourceRead:
    classic_source = get_classic_source_or_404(session, classic_source_id)
    return archive_classic_source(session, classic_source=classic_source)


@router.post(
    "/sources/{classic_source_id}/adapt",
    response_model=ClassicDraftBundleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Buddybug adaptation draft from a classic source",
)
def post_create_classic_adaptation(
    classic_source_id: int,
    payload: ClassicAdaptationCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ClassicDraftBundleResponse:
    classic_source = get_classic_source_or_404(session, classic_source_id)
    classic_draft = create_classic_adaptation(
        session,
        current_user=current_user,
        classic_source=classic_source,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
        language=payload.language,
        adaptation_intensity=payload.adaptation_intensity,
        min_pages=payload.min_pages,
        max_pages=payload.max_pages,
    )
    source, story_draft, story_pages, preview_book, preview_pages = get_classic_draft_bundle(session, classic_draft=classic_draft)
    return ClassicDraftBundleResponse(
        source=ClassicSourceRead.model_validate(source),
        adaptation=ClassicAdaptationDraftRead.model_validate(classic_draft),
        story_draft=StoryDraftRead.model_validate(story_draft) if story_draft is not None else None,
        story_pages=[StoryPageRead.model_validate(page) for page in story_pages],
        preview_book=BookRead.model_validate(preview_book) if preview_book is not None else None,
        preview_pages=[BookPageRead.model_validate(page) for page in preview_pages],
    )


@router.get("/drafts", response_model=list[ClassicAdaptationDraftRead], summary="List classic adaptation drafts")
def get_classic_drafts(
    classic_source_id: int | None = Query(default=None),
    review_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[ClassicAdaptationDraftRead]:
    return list_classic_adaptations(
        session,
        classic_source_id=classic_source_id,
        review_status=review_status,
        limit=limit,
    )


@router.get("/drafts/{classic_adaptation_draft_id}", response_model=ClassicDraftBundleResponse, summary="Get classic draft bundle")
def get_classic_draft(
    classic_adaptation_draft_id: int,
    session: Session = Depends(get_session),
) -> ClassicDraftBundleResponse:
    classic_draft = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    source, story_draft, story_pages, preview_book, preview_pages = get_classic_draft_bundle(session, classic_draft=classic_draft)
    return ClassicDraftBundleResponse(
        source=ClassicSourceRead.model_validate(source),
        adaptation=ClassicAdaptationDraftRead.model_validate(classic_draft),
        story_draft=StoryDraftRead.model_validate(story_draft) if story_draft is not None else None,
        story_pages=[StoryPageRead.model_validate(page) for page in story_pages],
        preview_book=BookRead.model_validate(preview_book) if preview_book is not None else None,
        preview_pages=[BookPageRead.model_validate(page) for page in preview_pages],
    )


@router.patch("/drafts/{classic_adaptation_draft_id}", response_model=ClassicAdaptationDraftRead, summary="Update classic draft")
def patch_classic_draft(
    classic_adaptation_draft_id: int,
    payload: ClassicAdaptationUpdate,
    session: Session = Depends(get_session),
) -> ClassicAdaptationDraftRead:
    classic_draft = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    updated = update_classic_adaptation(
        session,
        classic_draft=classic_draft,
        adapted_title=payload.adapted_title,
        adapted_text=payload.adapted_text,
        adaptation_intensity=payload.adaptation_intensity,
        adaptation_notes=payload.adaptation_notes,
        cameo_insertions_summary=payload.cameo_insertions_summary,
        scene_seed_notes_json=payload.scene_seed_notes_json,
        validation_status=payload.validation_status,
        validation_warnings_json=payload.validation_warnings_json,
        review_status=payload.review_status,
        illustration_status=payload.illustration_status,
        editor_notes=payload.editor_notes,
    )
    return ClassicAdaptationDraftRead.model_validate(updated)


@router.post("/drafts/{classic_adaptation_draft_id}/preview-book", response_model=ClassicDraftBundleResponse, summary="Rebuild classic preview book")
def post_classic_preview_book(
    classic_adaptation_draft_id: int,
    session: Session = Depends(get_session),
) -> ClassicDraftBundleResponse:
    classic_draft = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    rebuild_classic_preview_book(session, classic_draft=classic_draft)
    source, story_draft, story_pages, preview_book, preview_pages = get_classic_draft_bundle(session, classic_draft=classic_draft)
    return ClassicDraftBundleResponse(
        source=ClassicSourceRead.model_validate(source),
        adaptation=ClassicAdaptationDraftRead.model_validate(classic_draft),
        story_draft=StoryDraftRead.model_validate(story_draft) if story_draft is not None else None,
        story_pages=[StoryPageRead.model_validate(page) for page in story_pages],
        preview_book=BookRead.model_validate(preview_book) if preview_book is not None else None,
        preview_pages=[BookPageRead.model_validate(page) for page in preview_pages],
    )


@router.post(
    "/drafts/{classic_adaptation_draft_id}/generate-illustrations",
    response_model=ClassicIllustrationGenerationResponse,
    summary="Generate illustrations for a classic draft",
)
def post_classic_generate_illustrations(
    classic_adaptation_draft_id: int,
    session: Session = Depends(get_session),
) -> ClassicIllustrationGenerationResponse:
    classic_draft = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    return ClassicIllustrationGenerationResponse(**generate_classic_illustrations(session, classic_draft=classic_draft))


@router.post("/drafts/{classic_adaptation_draft_id}/approve", response_model=ClassicAdaptationDraftRead, summary="Approve classic draft")
def post_classic_approve(
    classic_adaptation_draft_id: int,
    payload: ClassicApproveRequest | None = None,
    session: Session = Depends(get_session),
) -> ClassicAdaptationDraftRead:
    classic_draft = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    approved = approve_classic_adaptation(
        session,
        classic_draft=classic_draft,
        editor_notes=payload.editor_notes if payload is not None else None,
    )
    return ClassicAdaptationDraftRead.model_validate(approved)


@router.post("/drafts/{classic_adaptation_draft_id}/archive", response_model=ClassicAdaptationDraftRead, summary="Archive classic draft")
def post_classic_archive(
    classic_adaptation_draft_id: int,
    session: Session = Depends(get_session),
) -> ClassicAdaptationDraftRead:
    classic_draft = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    return ClassicAdaptationDraftRead.model_validate(archive_classic_adaptation(session, classic_draft=classic_draft))


@router.post("/drafts/{classic_adaptation_draft_id}/publish", response_model=ClassicPublishResponse, summary="Publish classic draft")
def post_classic_publish(
    classic_adaptation_draft_id: int,
    session: Session = Depends(get_session),
) -> ClassicPublishResponse:
    classic_draft = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    book = publish_classic_adaptation(session, classic_draft=classic_draft)
    source = get_classic_source_or_404(session, classic_draft.classic_source_id)
    refreshed = get_classic_adaptation_or_404(session, classic_adaptation_draft_id)
    return ClassicPublishResponse(
        source=ClassicSourceRead.model_validate(source),
        adaptation=ClassicAdaptationDraftRead.model_validate(refreshed),
        book=BookRead.model_validate(book),
    )
