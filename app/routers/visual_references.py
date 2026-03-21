from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.visual_reference_schema import (
    VisualReferenceAssetCreate,
    VisualReferenceImportResponse,
    VisualReferenceAssetRead,
    VisualReferenceAssetUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.visual_reference_import_service import (
    build_character_bible_manifest,
    ensure_visual_reference_tables,
    import_entries,
)
from app.services.visual_reference_service import (
    create_visual_reference_asset,
    delete_visual_reference_asset,
    get_visual_reference_asset_or_404,
    list_recommended_visual_references_for_story_page,
    get_visual_references_by_target,
    list_visual_reference_assets,
    list_recommended_visual_references_for_story_draft,
    update_visual_reference_asset,
)
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/admin/visual-references", tags=["visual-references"])


@router.get("", response_model=list[VisualReferenceAssetRead], summary="List visual reference assets")
def get_visual_reference_assets(
    reference_type: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: int | None = Query(default=None),
    language: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[VisualReferenceAssetRead]:
    return list_visual_reference_assets(
        session,
        reference_type=reference_type,
        target_type=target_type,
        target_id=target_id,
        language=language,
        is_active=is_active,
        limit=limit,
    )


@router.get("/by-target", response_model=list[VisualReferenceAssetRead], summary="List visual reference assets for one target")
def get_visual_reference_assets_by_target(
    target_type: str = Query(...),
    target_id: int = Query(...),
    include_inactive: bool = Query(default=False),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[VisualReferenceAssetRead]:
    return get_visual_references_by_target(
        session,
        target_type=target_type,
        target_id=target_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/recommended-for-draft/{story_draft_id}",
    response_model=list[VisualReferenceAssetRead],
    summary="List recommended visual reference assets for one story draft",
)
def get_recommended_visual_reference_assets_for_draft(
    story_draft_id: int,
    include_inactive: bool = Query(default=False),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[VisualReferenceAssetRead]:
    return list_recommended_visual_references_for_story_draft(
        session,
        story_draft_id=story_draft_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/recommended-for-page/{story_page_id}",
    response_model=list[VisualReferenceAssetRead],
    summary="List recommended visual reference assets for one story page",
)
def get_recommended_visual_reference_assets_for_page(
    story_page_id: int,
    include_inactive: bool = Query(default=False),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[VisualReferenceAssetRead]:
    return list_recommended_visual_references_for_story_page(
        session,
        story_page_id=story_page_id,
        include_inactive=include_inactive,
    )


@router.post("", response_model=VisualReferenceAssetRead, status_code=status.HTTP_201_CREATED, summary="Create visual reference asset")
def post_visual_reference_asset(
    payload: VisualReferenceAssetCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> VisualReferenceAssetRead:
    asset = create_visual_reference_asset(
        session,
        name=payload.name,
        reference_type=payload.reference_type,
        target_type=payload.target_type,
        target_id=payload.target_id,
        image_url=payload.image_url,
        prompt_notes=payload.prompt_notes,
        language=payload.language,
        is_active=payload.is_active,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="visual_reference_asset_created",
        entity_type="visual_reference_asset",
        entity_id=str(asset.id),
        summary=f"Created visual reference asset '{asset.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return asset


@router.post(
    "/import-character-bible",
    response_model=VisualReferenceImportResponse,
    summary="Import visual references from the BuddyBug Character Bible artwork folder",
)
def import_character_bible_visual_references(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> VisualReferenceImportResponse:
    created_tables = ensure_visual_reference_tables()
    manifest = build_character_bible_manifest()
    result = import_entries(session, manifest, dry_run=False)
    create_audit_log(
        session,
        action_type="visual_reference_character_bible_imported",
        entity_type="visual_reference_asset",
        entity_id=None,
        summary="Imported visual references from the BuddyBug Character Bible",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={
            "created": result.created,
            "updated": result.updated,
            "scanned": result.scanned,
            "created_tables": created_tables,
        },
    )
    return VisualReferenceImportResponse(
        created=result.created,
        updated=result.updated,
        scanned=result.scanned,
        created_tables=created_tables,
    )


@router.patch("/{asset_id}", response_model=VisualReferenceAssetRead, summary="Update visual reference asset")
def patch_visual_reference_asset(
    asset_id: int,
    payload: VisualReferenceAssetUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> VisualReferenceAssetRead:
    asset = get_visual_reference_asset_or_404(session, asset_id=asset_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_visual_reference_asset(
        session,
        asset=asset,
        name=update_data.get("name"),
        reference_type=update_data.get("reference_type"),
        target_type=update_data.get("target_type"),
        target_id=update_data.get("target_id"),
        image_url=update_data.get("image_url"),
        prompt_notes=update_data.get("prompt_notes"),
        language=update_data.get("language"),
        is_active=update_data.get("is_active"),
        target_type_provided="target_type" in update_data,
        target_id_provided="target_id" in update_data,
        prompt_notes_provided="prompt_notes" in update_data,
        language_provided="language" in update_data,
    )
    create_audit_log(
        session,
        action_type="visual_reference_asset_updated",
        entity_type="visual_reference_asset",
        entity_id=str(updated.id),
        summary=f"Updated visual reference asset '{updated.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete visual reference asset")
def remove_visual_reference_asset(
    asset_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> Response:
    asset = get_visual_reference_asset_or_404(session, asset_id=asset_id)
    create_audit_log(
        session,
        action_type="visual_reference_asset_deleted",
        entity_type="visual_reference_asset",
        entity_id=str(asset.id),
        summary=f"Deleted visual reference asset '{asset.name}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"target_type": asset.target_type, "target_id": asset.target_id},
    )
    delete_visual_reference_asset(session, asset=asset)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
