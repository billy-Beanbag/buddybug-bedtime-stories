from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session, desc, select

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import Illustration, StoryPage, User
from app.schemas.illustration_schema import (
    IllustrationApprovalRequest,
    IllustrationCreate,
    IllustrationGenerateRequest,
    IllustrationGenerateResponse,
    IllustrationReferenceAssetRead,
    IllustrationPromptPackageRead,
    IllustrationPromptPreviewRequest,
    IllustrationRead,
    IllustrationUpdate,
)
from app.services.illustration_generation_service import build_illustration_generation_package
from app.services.audit_service import create_audit_log
from app.services.illustration_generator import (
    approve_illustration,
    generate_illustration_asset,
    get_illustration_or_404,
    resolve_provider,
    get_story_page_or_404,
    persist_illustration,
    reject_illustration,
    set_story_page_status_from_latest_illustration,
    validate_approval_status,
    validate_provider,
)
from app.services.review_service import utc_now
from app.services.story_quality_service import evaluate_illustration_quality
from app.utils.dependencies import get_current_editor_user

router = APIRouter(
    prefix="/illustrations",
    tags=["illustrations"],
    dependencies=[Depends(get_current_editor_user)],
)


@router.get("", response_model=list[IllustrationRead], summary="List illustration assets")
def list_illustrations(
    story_page_id: int | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> list[Illustration]:
    statement = select(Illustration).order_by(desc(Illustration.created_at)).limit(limit)
    if story_page_id is not None:
        statement = statement.where(Illustration.story_page_id == story_page_id)
    if approval_status:
        validate_approval_status(approval_status)
        statement = statement.where(Illustration.approval_status == approval_status)
    return list(session.exec(statement).all())


@router.get(
    "/by-page/{story_page_id}",
    response_model=list[IllustrationRead],
    summary="Get illustration versions for one story page",
)
def get_illustrations_by_page(
    story_page_id: int,
    session: Session = Depends(get_session),
) -> list[Illustration]:
    get_story_page_or_404(session, story_page_id)
    statement = (
        select(Illustration)
        .where(Illustration.story_page_id == story_page_id)
        .order_by(desc(Illustration.version_number), desc(Illustration.created_at))
    )
    return list(session.exec(statement).all())


@router.get(
    "/by-draft/{story_draft_id}",
    response_model=list[IllustrationRead],
    summary="Get illustration assets for all pages in one story draft",
)
def get_illustrations_by_draft(
    story_draft_id: int,
    session: Session = Depends(get_session),
) -> list[Illustration]:
    page_statement = (
        select(StoryPage.id)
        .where(StoryPage.story_draft_id == story_draft_id)
        .order_by(StoryPage.page_number)
    )
    page_ids = list(session.exec(page_statement).all())
    if not page_ids:
        return []

    illustrations = list(
        session.exec(select(Illustration).where(Illustration.story_page_id.in_(page_ids))).all()
    )
    page_order = {page_id: idx for idx, page_id in enumerate(page_ids)}
    illustrations.sort(
        key=lambda item: (page_order.get(item.story_page_id, 10**9), -item.version_number, -item.id)
    )
    return illustrations


@router.post(
    "/generate/preview",
    response_model=IllustrationPromptPackageRead,
    summary="Preview the structured prompt package for a story page illustration",
)
def preview_illustration_generation_package(
    payload: IllustrationPromptPreviewRequest,
    session: Session = Depends(get_session),
) -> IllustrationPromptPackageRead:
    story_page = get_story_page_or_404(session, payload.story_page_id)
    provider = resolve_provider(payload.provider)
    package = build_illustration_generation_package(
        session=session,
        story_page=story_page,
        provider=provider,
        override_prompt=payload.override_prompt,
    )
    return IllustrationPromptPackageRead(
        story_page_id=package.story_page_id,
        provider=package.provider,
        provider_model=package.provider_model,
        provider_base_url=package.provider_base_url,
        provider_timeout_seconds=package.provider_timeout_seconds,
        generation_ready=package.generation_ready,
        live_generation_available=package.live_generation_available,
        debug_enabled=package.debug_enabled,
        prompt_used=package.prompt_used,
        positive_prompt=package.positive_prompt,
        negative_prompt=package.negative_prompt,
        page_text=package.page_text,
        scene_summary=package.scene_summary,
        location=package.location,
        mood=package.mood,
        characters_present=package.characters_present,
        reference_assets=[
            IllustrationReferenceAssetRead(
                id=asset.id,
                name=asset.name,
                reference_type=asset.reference_type,
                target_type=asset.target_type,
                target_id=asset.target_id,
                image_url=asset.image_url,
                prompt_notes=asset.prompt_notes,
                language=asset.language,
                is_active=asset.is_active,
            )
            for asset in package.reference_assets
        ],
        reference_summary=package.reference_summary,
    )


@router.post(
    "/generate",
    response_model=IllustrationGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate an illustration asset for a story page",
)
def generate_illustration(
    payload: IllustrationGenerateRequest,
    session: Session = Depends(get_session),
) -> IllustrationGenerateResponse:
    story_page = get_story_page_or_404(session, payload.story_page_id)
    illustration = generate_illustration_asset(
        session,
        story_page=story_page,
        provider=payload.provider,
        override_prompt=payload.override_prompt,
        generation_notes=payload.generation_notes,
    )
    evaluate_illustration_quality(session, illustration_id=illustration.id)
    refreshed_page = get_story_page_or_404(session, payload.story_page_id)
    return IllustrationGenerateResponse(
        illustration=illustration,
        story_page_id=refreshed_page.id,
        image_status=refreshed_page.image_status,
    )


@router.post(
    "",
    response_model=IllustrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create one illustration asset manually",
)
def create_illustration(
    payload: IllustrationCreate,
    session: Session = Depends(get_session),
) -> Illustration:
    story_page = get_story_page_or_404(session, payload.story_page_id)
    validate_approval_status(payload.approval_status)
    validate_provider(payload.provider)
    illustration = Illustration.model_validate(payload)
    illustration = persist_illustration(session, illustration)
    set_story_page_status_from_latest_illustration(session, story_page)
    return illustration


@router.get("/{illustration_id}", response_model=IllustrationRead, summary="Get one illustration asset by id")
def get_illustration(illustration_id: int, session: Session = Depends(get_session)) -> Illustration:
    return get_illustration_or_404(session, illustration_id)


@router.patch(
    "/{illustration_id}",
    response_model=IllustrationRead,
    summary="Partially update one illustration asset",
)
def update_illustration(
    illustration_id: int,
    payload: IllustrationUpdate,
    session: Session = Depends(get_session),
) -> Illustration:
    illustration = get_illustration_or_404(session, illustration_id)
    original_story_page_id = illustration.story_page_id
    update_data = payload.model_dump(exclude_unset=True)

    if "story_page_id" in update_data and update_data["story_page_id"] is not None:
        get_story_page_or_404(session, update_data["story_page_id"])
    if "approval_status" in update_data and update_data["approval_status"] is not None:
        validate_approval_status(update_data["approval_status"])
    if "provider" in update_data and update_data["provider"] is not None:
        validate_provider(update_data["provider"])

    for field_name, value in update_data.items():
        setattr(illustration, field_name, value)

    illustration.updated_at = utc_now()
    illustration = persist_illustration(session, illustration)
    set_story_page_status_from_latest_illustration(session, get_story_page_or_404(session, illustration.story_page_id))
    if illustration.story_page_id != original_story_page_id:
        set_story_page_status_from_latest_illustration(session, get_story_page_or_404(session, original_story_page_id))
    return illustration


@router.delete(
    "/{illustration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one illustration asset",
)
def delete_illustration(illustration_id: int, session: Session = Depends(get_session)) -> Response:
    illustration = get_illustration_or_404(session, illustration_id)
    story_page_id = illustration.story_page_id
    session.delete(illustration)
    session.commit()
    set_story_page_status_from_latest_illustration(session, get_story_page_or_404(session, story_page_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{illustration_id}/approve",
    response_model=IllustrationRead,
    summary="Approve an illustration asset",
)
def approve_illustration_asset(
    illustration_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> Illustration:
    illustration = get_illustration_or_404(session, illustration_id)
    approved = approve_illustration(session, illustration)
    create_audit_log(
        session,
        action_type="illustration_approved",
        entity_type="illustration",
        entity_id=str(approved.id),
        summary=f"Approved illustration {approved.id} for story page {approved.story_page_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"story_page_id": approved.story_page_id, "version_number": approved.version_number},
    )
    return approved


@router.post(
    "/{illustration_id}/reject",
    response_model=IllustrationRead,
    summary="Reject an illustration asset",
)
def reject_illustration_asset(
    illustration_id: int,
    request: Request,
    payload: IllustrationApprovalRequest | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> Illustration:
    illustration = get_illustration_or_404(session, illustration_id)
    generation_notes = payload.generation_notes if payload is not None else None
    rejected = reject_illustration(session, illustration, generation_notes=generation_notes)
    create_audit_log(
        session,
        action_type="illustration_rejected",
        entity_type="illustration",
        entity_id=str(rejected.id),
        summary=f"Rejected illustration {rejected.id} for story page {rejected.story_page_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"story_page_id": rejected.story_page_id, "generation_notes": generation_notes},
    )
    return rejected
