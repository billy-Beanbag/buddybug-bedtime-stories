from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import BookPage, User
from app.schemas.book_schema import BookPageRead, BookRead
from app.schemas.editorial_schema import (
    EditorialAssetCreate,
    EditorialAssetRead,
    EditorialAssetUpdate,
    EditorialProjectCreate,
    EditorialProjectDraftResponse,
    EditorialProjectRead,
    EditorialProjectUpdate,
    EditorialQualityRunResponse,
    ManualStoryDraftCreate,
    ManualStoryDraftUpdate,
    ManualStoryPageCreate,
    ManualStoryPageUpdate,
    PreviewBookResponse,
)
from app.schemas.quality_schema import QualityCheckRead
from app.schemas.story_schema import StoryDraftRead, StoryPageRead
from app.services.audit_service import create_audit_log
from app.services.editorial_service import (
    archive_editorial_project,
    build_preview_book,
    create_editorial_asset,
    create_editorial_project,
    create_manual_story_draft,
    create_manual_story_page,
    delete_editorial_asset,
    get_editorial_asset_or_404,
    get_editorial_draft_or_404,
    get_editorial_project_or_404,
    get_editorial_story_page_or_404,
    get_project_draft_bundle,
    list_editorial_assets,
    list_editorial_projects,
    list_story_pages_for_draft,
    mark_project_ready_for_publish,
    publish_project,
    run_editorial_quality_checks,
    update_editorial_asset,
    update_editorial_project,
    update_manual_story_draft,
    update_manual_story_page,
)
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/editorial", tags=["editorial"])


@router.get("/projects", response_model=list[EditorialProjectRead], summary="List editorial projects")
def get_editorial_projects(
    status_value: str | None = Query(default=None, alias="status"),
    source_type: str | None = Query(default=None),
    language: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[EditorialProjectRead]:
    return list_editorial_projects(
        session,
        status_value=status_value,
        source_type=source_type,
        language=language,
        limit=limit,
    )


@router.get("/projects/{project_id}", response_model=EditorialProjectRead, summary="Get one editorial project")
def get_editorial_project(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> EditorialProjectRead:
    return get_editorial_project_or_404(session, project_id)


@router.post("/projects", response_model=EditorialProjectRead, status_code=status.HTTP_201_CREATED, summary="Create editorial project")
def post_editorial_project(
    payload: EditorialProjectCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> EditorialProjectRead:
    project = create_editorial_project(
        session,
        current_user=current_user,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
        language=payload.language,
        status_value=payload.status,
        assigned_editor_user_id=payload.assigned_editor_user_id,
        source_type=payload.source_type,
        notes=payload.notes,
    )
    create_audit_log(
        session,
        action_type="editorial_project_created",
        entity_type="editorial_project",
        entity_id=str(project.id),
        summary=f"Created editorial project '{project.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"status": project.status, "source_type": project.source_type},
    )
    return project


@router.patch("/projects/{project_id}", response_model=EditorialProjectRead, summary="Update editorial project")
def patch_editorial_project(
    project_id: int,
    payload: EditorialProjectUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> EditorialProjectRead:
    project = get_editorial_project_or_404(session, project_id)
    updated = update_editorial_project(
        session,
        project=project,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
        language=payload.language,
        status_value=payload.status,
        assigned_editor_user_id=payload.assigned_editor_user_id,
        source_type=payload.source_type,
        notes=payload.notes,
    )
    create_audit_log(
        session,
        action_type="editorial_project_updated",
        entity_type="editorial_project",
        entity_id=str(updated.id),
        summary=f"Updated editorial project '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Archive editorial project")
def delete_editorial_project(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> Response:
    project = get_editorial_project_or_404(session, project_id)
    archive_editorial_project(session, project=project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/projects/{project_id}/assets", response_model=list[EditorialAssetRead], summary="List project editorial assets")
def get_project_assets(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[EditorialAssetRead]:
    get_editorial_project_or_404(session, project_id)
    return list_editorial_assets(session, project_id=project_id)


@router.post("/projects/{project_id}/assets", response_model=EditorialAssetRead, status_code=status.HTTP_201_CREATED, summary="Add project asset")
def post_project_asset(
    project_id: int,
    payload: EditorialAssetCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> EditorialAssetRead:
    project = get_editorial_project_or_404(session, project_id)
    asset = create_editorial_asset(
        session,
        current_user=current_user,
        project=project,
        asset_type=payload.asset_type,
        file_url=payload.file_url,
        language=payload.language,
        page_number=payload.page_number,
        is_active=payload.is_active,
    )
    create_audit_log(
        session,
        action_type="editorial_asset_added",
        entity_type="editorial_asset",
        entity_id=str(asset.id),
        summary=f"Added {asset.asset_type} asset to project {project.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"project_id": project.id, "page_number": asset.page_number},
    )
    return asset


@router.patch("/assets/{asset_id}", response_model=EditorialAssetRead, summary="Update editorial asset")
def patch_editorial_asset(
    asset_id: int,
    payload: EditorialAssetUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> EditorialAssetRead:
    asset = get_editorial_asset_or_404(session, asset_id)
    return update_editorial_asset(
        session,
        asset=asset,
        asset_type=payload.asset_type,
        file_url=payload.file_url,
        language=payload.language,
        page_number=payload.page_number,
        is_active=payload.is_active,
    )


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete editorial asset")
def remove_editorial_asset(
    asset_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> Response:
    asset = get_editorial_asset_or_404(session, asset_id)
    delete_editorial_asset(session, asset=asset)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/projects/{project_id}/draft", response_model=EditorialProjectDraftResponse, summary="Get project draft, pages, and preview book")
def get_project_draft_state(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> EditorialProjectDraftResponse:
    get_editorial_project_or_404(session, project_id)
    draft, pages, preview_book = get_project_draft_bundle(session, project_id=project_id)
    return EditorialProjectDraftResponse(
        draft=StoryDraftRead.model_validate(draft) if draft is not None else None,
        pages=[StoryPageRead.model_validate(page) for page in pages],
        preview_book=BookRead.model_validate(preview_book) if preview_book is not None else None,
    )


@router.post("/story-drafts", response_model=StoryDraftRead, status_code=status.HTTP_201_CREATED, summary="Create manual story draft")
def post_manual_story_draft(
    payload: ManualStoryDraftCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryDraftRead:
    draft = create_manual_story_draft(
        session,
        title=payload.title,
        full_text=payload.full_text,
        summary=payload.summary,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
        language=payload.language,
        review_status=payload.review_status,
        project_id=payload.project_id,
        read_time_minutes=payload.read_time_minutes,
    )
    create_audit_log(
        session,
        action_type="manual_story_draft_created",
        entity_type="story_draft",
        entity_id=str(draft.id),
        summary=f"Created manual story draft '{draft.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"project_id": draft.project_id},
    )
    return draft


@router.patch("/story-drafts/{draft_id}", response_model=StoryDraftRead, summary="Update manual story draft")
def patch_manual_story_draft(
    draft_id: int,
    payload: ManualStoryDraftUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryDraftRead:
    draft = get_editorial_draft_or_404(session, draft_id)
    return update_manual_story_draft(
        session,
        draft=draft,
        created_by_user_id=current_user.id,
        title=payload.title,
        full_text=payload.full_text,
        summary=payload.summary,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
        language=payload.language,
        review_status=payload.review_status,
        project_id=payload.project_id,
        read_time_minutes=payload.read_time_minutes,
        review_notes=payload.review_notes,
        approved_text=payload.approved_text,
    )


@router.post("/story-pages", response_model=StoryPageRead, status_code=status.HTTP_201_CREATED, summary="Create manual story page")
def post_manual_story_page(
    payload: ManualStoryPageCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryPageRead:
    page = create_manual_story_page(
        session,
        story_draft_id=payload.story_draft_id,
        page_number=payload.page_number,
        page_text=payload.page_text,
        scene_summary=payload.scene_summary,
        location=payload.location,
        mood=payload.mood,
        characters_present=payload.characters_present,
        illustration_prompt=payload.illustration_prompt,
        image_url=payload.image_url,
    )
    create_audit_log(
        session,
        action_type="manual_story_page_updated",
        entity_type="story_page",
        entity_id=str(page.id),
        summary=f"Created manual story page {page.page_number}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"story_draft_id": page.story_draft_id},
    )
    return page


@router.patch("/story-pages/{page_id}", response_model=StoryPageRead, summary="Update manual story page")
def patch_manual_story_page(
    page_id: int,
    payload: ManualStoryPageUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StoryPageRead:
    page = get_editorial_story_page_or_404(session, page_id)
    updated = update_manual_story_page(
        session,
        page=page,
        created_by_user_id=current_user.id,
        page_number=payload.page_number,
        page_text=payload.page_text,
        scene_summary=payload.scene_summary,
        location=payload.location,
        mood=payload.mood,
        characters_present=payload.characters_present,
        illustration_prompt=payload.illustration_prompt,
        image_url=payload.image_url,
    )
    create_audit_log(
        session,
        action_type="manual_story_page_updated",
        entity_type="story_page",
        entity_id=str(updated.id),
        summary=f"Updated manual story page {updated.page_number}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@router.get("/story-drafts/{draft_id}/pages", response_model=list[StoryPageRead], summary="List ordered story pages for one draft")
def get_manual_story_draft_pages(
    draft_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[StoryPageRead]:
    get_editorial_draft_or_404(session, draft_id)
    return list_story_pages_for_draft(session, story_draft_id=draft_id)


@router.post("/story-drafts/{draft_id}/build-preview", response_model=PreviewBookResponse, summary="Build or update preview book")
def post_build_preview_book(
    draft_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> PreviewBookResponse:
    draft = get_editorial_draft_or_404(session, draft_id)
    book, pages = build_preview_book(session, draft=draft)
    create_audit_log(
        session,
        action_type="editorial_preview_built",
        entity_type="book",
        entity_id=str(book.id),
        summary=f"Built preview book for draft {draft.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"draft_id": draft.id, "preview_only": True},
    )
    return PreviewBookResponse(
        book=BookRead.model_validate(book),
        pages=[BookPageRead.model_validate(page) for page in pages],
        preview_only=True,
    )


@router.post("/projects/{project_id}/ready-for-publish", response_model=EditorialProjectRead, summary="Mark project ready for publish")
def post_ready_for_publish(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> EditorialProjectRead:
    project = get_editorial_project_or_404(session, project_id)
    return mark_project_ready_for_publish(session, project=project)


@router.post("/projects/{project_id}/publish", response_model=PreviewBookResponse, summary="Publish editorial project")
def post_publish_project(
    project_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> PreviewBookResponse:
    project = get_editorial_project_or_404(session, project_id)
    project, book = publish_project(session, project=project)
    create_audit_log(
        session,
        action_type="editorial_project_published",
        entity_type="editorial_project",
        entity_id=str(project.id),
        summary=f"Published editorial project '{project.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": book.id},
    )
    ordered_pages = session.exec(
        select(BookPage).where(BookPage.book_id == book.id).order_by(BookPage.page_number)
    ).all()
    return PreviewBookResponse(
        book=BookRead.model_validate(book),
        pages=[BookPageRead.model_validate(page) for page in ordered_pages],
        preview_only=False,
    )


@router.post("/story-drafts/{draft_id}/run-quality", response_model=EditorialQualityRunResponse, summary="Run quality checks for manual draft")
def post_run_editorial_quality(
    draft_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> EditorialQualityRunResponse:
    get_editorial_draft_or_404(session, draft_id)
    draft_checks, page_checks = run_editorial_quality_checks(session, story_draft_id=draft_id)
    return EditorialQualityRunResponse(
        draft_checks=[QualityCheckRead.model_validate(check) for check in draft_checks],
        page_checks=[QualityCheckRead.model_validate(check) for check in page_checks],
    )
