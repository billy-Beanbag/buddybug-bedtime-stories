from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.changelog_schema import ChangelogEntryCreate, ChangelogEntryRead, ChangelogEntryUpdate
from app.services.audit_service import create_audit_log
from app.services.changelog_service import (
    archive_changelog_entry,
    create_changelog_entry,
    get_changelog_entry_or_404,
    list_changelog_entries,
    publish_changelog_entry,
    update_changelog_entry,
)
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/changelog", tags=["changelog"])
admin_router = APIRouter(prefix="/admin/changelog", tags=["admin-changelog"])


@router.get("", response_model=list[ChangelogEntryRead], summary="List published user-facing changelog entries")
def get_public_changelog(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[ChangelogEntryRead]:
    return list_changelog_entries(
        session,
        audience="user_facing",
        status_value="published",
        area_tag=None,
        feature_flag_key=None,
        limit=limit,
    )


@admin_router.get("", response_model=list[ChangelogEntryRead], summary="List changelog entries")
def get_admin_changelog(
    audience: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    area_tag: str | None = Query(default=None),
    feature_flag_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[ChangelogEntryRead]:
    return list_changelog_entries(
        session,
        audience=audience,
        status_value=status_value,
        area_tag=area_tag,
        feature_flag_key=feature_flag_key,
        limit=limit,
    )


@admin_router.post("", response_model=ChangelogEntryRead, status_code=status.HTTP_201_CREATED, summary="Create changelog entry")
def post_changelog_entry(
    payload: ChangelogEntryCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ChangelogEntryRead:
    entry = create_changelog_entry(
        session,
        version_label=payload.version_label,
        title=payload.title,
        summary=payload.summary,
        details_markdown=payload.details_markdown,
        audience=payload.audience,
        status_value=payload.status,
        area_tags=payload.area_tags,
        feature_flag_keys=payload.feature_flag_keys,
        published_at=payload.published_at,
        created_by_user_id=current_user.id,
    )
    create_audit_log(
        session,
        action_type="changelog_entry_created",
        entity_type="changelog_entry",
        entity_id=str(entry.id),
        summary=f"Created changelog entry '{entry.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(mode="json"),
    )
    return entry


@admin_router.patch("/{entry_id}", response_model=ChangelogEntryRead, summary="Update changelog entry")
def patch_changelog_entry(
    entry_id: int,
    payload: ChangelogEntryUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ChangelogEntryRead:
    entry = get_changelog_entry_or_404(session, entry_id=entry_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated = update_changelog_entry(
        session,
        entry=entry,
        version_label=update_data.get("version_label"),
        title=update_data.get("title"),
        summary=update_data.get("summary"),
        details_markdown=update_data.get("details_markdown"),
        audience=update_data.get("audience"),
        status_value=update_data.get("status"),
        area_tags=update_data.get("area_tags"),
        feature_flag_keys=update_data.get("feature_flag_keys"),
        published_at=update_data.get("published_at"),
        details_markdown_provided="details_markdown" in update_data,
        area_tags_provided="area_tags" in update_data,
        feature_flag_keys_provided="feature_flag_keys" in update_data,
        published_at_provided="published_at" in update_data,
    )
    create_audit_log(
        session,
        action_type="changelog_entry_updated",
        entity_type="changelog_entry",
        entity_id=str(updated.id),
        summary=f"Updated changelog entry '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=update_data,
    )
    return updated


@admin_router.post("/{entry_id}/publish", response_model=ChangelogEntryRead, summary="Publish changelog entry")
def publish_entry(
    entry_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ChangelogEntryRead:
    entry = get_changelog_entry_or_404(session, entry_id=entry_id)
    published = publish_changelog_entry(session, entry=entry)
    create_audit_log(
        session,
        action_type="changelog_entry_published",
        entity_type="changelog_entry",
        entity_id=str(published.id),
        summary=f"Published changelog entry '{published.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"audience": published.audience, "published_at": published.published_at},
    )
    return published


@admin_router.post("/{entry_id}/archive", response_model=ChangelogEntryRead, summary="Archive changelog entry")
def archive_entry(
    entry_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> ChangelogEntryRead:
    entry = get_changelog_entry_or_404(session, entry_id=entry_id)
    archived = archive_changelog_entry(session, entry=entry)
    create_audit_log(
        session,
        action_type="changelog_entry_archived",
        entity_type="changelog_entry",
        entity_id=str(archived.id),
        summary=f"Archived changelog entry '{archived.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"audience": archived.audience},
    )
    return archived
