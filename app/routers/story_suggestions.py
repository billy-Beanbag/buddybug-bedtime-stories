from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import ChildProfile, StoryIdea, StorySuggestion, User
from app.schemas.story_suggestion_schema import (
    StorySuggestionAdminListResponse,
    StorySuggestionAdminRead,
    StorySuggestionAdminUpdate,
    StorySuggestionCreate,
    StorySuggestionListResponse,
    StorySuggestionRead,
)
from app.services.audit_service import create_audit_log
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.content_lane_service import validate_content_lane_key
from app.services.i18n_service import validate_language_code
from app.services.review_service import utc_now
from app.services.subscription_service import has_premium_access
from app.utils.dependencies import get_current_active_user, get_current_editor_user

ALLOWED_STORY_SUGGESTION_STATUSES = {"submitted", "in_review", "approved", "archived"}

router = APIRouter(prefix="/story-suggestions", tags=["story-suggestions"])
admin_router = APIRouter(prefix="/admin/story-suggestions", tags=["admin-story-suggestions"])


def _validate_status(status_value: str | None) -> str | None:
    if status_value is None:
        return None
    if status_value not in ALLOWED_STORY_SUGGESTION_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid story suggestion status")
    return status_value


def _require_premium_access(current_user: User) -> None:
    if not has_premium_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium access is required to submit story suggestions",
        )


def _get_story_suggestion_or_404(session: Session, suggestion_id: int) -> StorySuggestion:
    suggestion = session.get(StorySuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story suggestion not found")
    return suggestion


def _build_admin_read(session: Session, suggestion: StorySuggestion) -> StorySuggestionAdminRead:
    user = session.get(User, suggestion.user_id)
    child_profile = session.get(ChildProfile, suggestion.child_profile_id) if suggestion.child_profile_id else None
    promoted_story_idea = session.get(StoryIdea, suggestion.promoted_story_idea_id) if suggestion.promoted_story_idea_id else None
    return StorySuggestionAdminRead(
        id=suggestion.id,
        user_id=suggestion.user_id,
        child_profile_id=suggestion.child_profile_id,
        promoted_story_idea_id=suggestion.promoted_story_idea_id,
        title=suggestion.title,
        brief=suggestion.brief,
        desired_outcome=suggestion.desired_outcome,
        inspiration_notes=suggestion.inspiration_notes,
        avoid_notes=suggestion.avoid_notes,
        age_band=suggestion.age_band,
        language=suggestion.language,
        allow_reference_use=suggestion.allow_reference_use,
        status=suggestion.status,
        approved_as_reference=suggestion.approved_as_reference,
        editorial_notes=suggestion.editorial_notes,
        created_at=suggestion.created_at,
        updated_at=suggestion.updated_at,
        user_email=user.email if user is not None else None,
        user_display_name=user.display_name if user is not None else None,
        child_profile_name=child_profile.display_name if child_profile is not None else None,
        promoted_story_idea_title=promoted_story_idea.title if promoted_story_idea is not None else None,
    )


def _derive_story_idea_title(suggestion: StorySuggestion) -> str:
    if suggestion.title and suggestion.title.strip():
        return suggestion.title.strip()
    brief = suggestion.brief.strip()
    if not brief:
        return "Parent suggested story"
    trimmed = brief.split(".")[0].strip() or brief
    if len(trimmed) <= 80:
        return trimmed
    shortened = trimmed[:77].rsplit(" ", 1)[0].strip()
    return f"{shortened or trimmed[:77].strip()}..."


def _build_promoted_story_idea(
    session: Session,
    *,
    suggestion: StorySuggestion,
    child_profile: ChildProfile | None,
) -> StoryIdea:
    lane = validate_content_lane_key(session, age_band=suggestion.age_band, content_lane_key=None)
    goal = (suggestion.desired_outcome or "").strip()
    include_notes = (suggestion.inspiration_notes or "").strip()
    combined_notes = " ".join(
        part for part in [suggestion.brief.strip(), include_notes, (suggestion.avoid_notes or "").strip(), goal] if part
    ).casefold()

    if "shortcut" in combined_notes or "quicker way" in combined_notes or "quick way" in combined_notes:
        hook_type = "clever_shortcut"
    elif any(token in combined_notes for token in ("spill", "spilled", "splash", "splashed", "mess", "muddy", "baking")):
        hook_type = "accidental_mess"
    elif any(token in combined_notes for token in ("race", "contest", "competition", "bet", "who can", "challenge")):
        hook_type = "silly_competition"
    elif any(token in combined_notes for token in ("plan", "organise", "organize", "set up", "help", "carry", "stack")):
        hook_type = "helpful_plan_goes_wrong"
    else:
        hook_type = "unexpected_discovery"

    if "zoo" in combined_notes:
        setting = "zoo picnic lawn"
    elif "picnic" in combined_notes:
        setting = "picnic meadow"
    elif "kitchen" in combined_notes or "baking" in combined_notes:
        setting = "family kitchen"
    elif "garden" in combined_notes:
        setting = "garden path"
    elif "bedroom" in combined_notes:
        setting = "bedroom"
    elif "park" in combined_notes or "playground" in combined_notes:
        setting = "park playground"
    elif "beach" in combined_notes:
        setting = "seaside beach"
    elif "library" in combined_notes:
        setting = "library reading nook"
    elif "school" in combined_notes:
        setting = "school playground"
    elif "farm" in combined_notes:
        setting = "farmyard path"
    else:
        setting = "garden path"

    if any(token in combined_notes for token in ("friend", "together", "share")):
        theme = "friendship"
    elif any(token in combined_notes for token in ("brave", "confidence", "confident")):
        theme = "confidence"
    elif any(token in combined_notes for token in ("kind", "gentle", "caring")):
        theme = "kindness"
    elif any(token in combined_notes for token in ("help", "team", "together")):
        theme = "teamwork"
    elif any(token in combined_notes for token in ("calm", "sleep", "bedtime")):
        theme = "reassurance"
    else:
        theme = "problem solving"

    bedtime_feeling = goal or "proud, reassured, and calm"
    main_characters = "Buddybug"
    supporting_characters = "Verity"

    return StoryIdea(
        title=_derive_story_idea_title(suggestion),
        premise=suggestion.brief.strip(),
        hook_type=hook_type,
        age_band=lane.age_band,
        content_lane_key=lane.key,
        tone="warm, grounded, child-led",
        setting=setting,
        theme=theme,
        bedtime_feeling=bedtime_feeling,
        main_characters=main_characters,
        supporting_characters=supporting_characters,
        estimated_minutes=6,
        status="idea_pending",
        generation_source="parent_suggestion",
    )


@router.get("/me", response_model=StorySuggestionListResponse, summary="List current user story suggestions")
def list_my_story_suggestions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> StorySuggestionListResponse:
    _require_premium_access(current_user)
    items = list(
        session.exec(
            select(StorySuggestion)
            .where(StorySuggestion.user_id == current_user.id)
            .order_by(StorySuggestion.created_at.desc())
        ).all()
    )
    return StorySuggestionListResponse(items=[StorySuggestionRead.model_validate(item) for item in items])


@router.post("", response_model=StorySuggestionRead, status_code=status.HTTP_201_CREATED, summary="Create a story suggestion")
def create_story_suggestion(
    payload: StorySuggestionCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> StorySuggestionRead:
    _require_premium_access(current_user)
    child_profile = validate_child_profile_ownership(
        session,
        user_id=current_user.id,
        child_profile_id=payload.child_profile_id,
    )
    suggestion = StorySuggestion(
        user_id=current_user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        title=payload.title.strip() if payload.title else None,
        brief=payload.brief.strip(),
        desired_outcome=payload.desired_outcome.strip() if payload.desired_outcome else None,
        inspiration_notes=payload.inspiration_notes.strip() if payload.inspiration_notes else None,
        avoid_notes=payload.avoid_notes.strip() if payload.avoid_notes else None,
        age_band=(child_profile.age_band if child_profile is not None else payload.age_band).strip(),
        language=validate_language_code(child_profile.language if child_profile is not None else payload.language),
        allow_reference_use=payload.allow_reference_use,
    )
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    create_audit_log(
        session,
        action_type="story_suggestion_created",
        entity_type="story_suggestion",
        entity_id=str(suggestion.id),
        summary=f"Created story suggestion {suggestion.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={
            "child_profile_id": suggestion.child_profile_id,
            "age_band": suggestion.age_band,
            "language": suggestion.language,
            "allow_reference_use": suggestion.allow_reference_use,
        },
    )
    return suggestion


@admin_router.get("", response_model=StorySuggestionAdminListResponse, summary="List story suggestions for staff review")
def list_story_suggestions_for_admin(
    status_value: str | None = Query(default=None, alias="status"),
    approved_as_reference: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> StorySuggestionAdminListResponse:
    validated_status = _validate_status(status_value)
    statement = select(StorySuggestion).order_by(StorySuggestion.created_at.desc()).limit(limit)
    if validated_status is not None:
        statement = statement.where(StorySuggestion.status == validated_status)
    if approved_as_reference is not None:
        statement = statement.where(StorySuggestion.approved_as_reference == approved_as_reference)
    items = list(session.exec(statement).all())
    return StorySuggestionAdminListResponse(items=[_build_admin_read(session, item) for item in items])


@admin_router.patch("/{suggestion_id}", response_model=StorySuggestionAdminRead, summary="Update a story suggestion")
def update_story_suggestion_for_admin(
    suggestion_id: int,
    payload: StorySuggestionAdminUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StorySuggestionAdminRead:
    suggestion = _get_story_suggestion_or_404(session, suggestion_id)
    if payload.status is not None:
        suggestion.status = _validate_status(payload.status) or suggestion.status
    if payload.editorial_notes is not None:
        suggestion.editorial_notes = payload.editorial_notes.strip() or None
    if payload.approved_as_reference is not None:
        if payload.approved_as_reference and not suggestion.allow_reference_use:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent permission is required before approving this suggestion as a reusable reference",
            )
        suggestion.approved_as_reference = payload.approved_as_reference
        if payload.approved_as_reference and suggestion.status == "submitted":
            suggestion.status = "approved"
    suggestion.updated_at = utc_now()
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    create_audit_log(
        session,
        action_type="story_suggestion_updated",
        entity_type="story_suggestion",
        entity_id=str(suggestion.id),
        summary=f"Updated story suggestion {suggestion.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return _build_admin_read(session, suggestion)


@admin_router.post(
    "/{suggestion_id}/promote-to-idea",
    response_model=StorySuggestionAdminRead,
    status_code=status.HTTP_201_CREATED,
    summary="Promote a story suggestion into the ideas queue",
)
def promote_story_suggestion_to_idea(
    suggestion_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> StorySuggestionAdminRead:
    suggestion = _get_story_suggestion_or_404(session, suggestion_id)
    existing_idea = session.get(StoryIdea, suggestion.promoted_story_idea_id) if suggestion.promoted_story_idea_id else None
    child_profile = session.get(ChildProfile, suggestion.child_profile_id) if suggestion.child_profile_id else None
    refreshed_story_idea = _build_promoted_story_idea(session, suggestion=suggestion, child_profile=child_profile)
    if existing_idea is not None:
        if existing_idea.status != "idea_pending":
            return _build_admin_read(session, suggestion)
        for field_name in (
            "title",
            "premise",
            "hook_type",
            "age_band",
            "content_lane_key",
            "tone",
            "setting",
            "theme",
            "bedtime_feeling",
            "main_characters",
            "supporting_characters",
            "estimated_minutes",
            "generation_source",
        ):
            setattr(existing_idea, field_name, getattr(refreshed_story_idea, field_name))
        existing_idea.updated_at = utc_now()
        session.add(existing_idea)
        session.commit()
        session.refresh(existing_idea)
        story_idea = existing_idea
    else:
        story_idea = refreshed_story_idea
        session.add(story_idea)
        session.commit()
        session.refresh(story_idea)

    suggestion.promoted_story_idea_id = story_idea.id
    if suggestion.status in {"submitted", "in_review"}:
        suggestion.status = "approved"
    suggestion.updated_at = utc_now()
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)

    create_audit_log(
        session,
        action_type="story_suggestion_promoted_to_idea",
        entity_type="story_suggestion",
        entity_id=str(suggestion.id),
        summary=f"Promoted story suggestion {suggestion.id} to story idea {story_idea.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"story_idea_id": story_idea.id},
    )
    return _build_admin_read(session, suggestion)


@admin_router.delete(
    "/{suggestion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a story suggestion",
)
def delete_story_suggestion_for_admin(
    suggestion_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
):
    suggestion = _get_story_suggestion_or_404(session, suggestion_id)
    suggestion_title = suggestion.title
    suggestion_user_id = suggestion.user_id
    session.delete(suggestion)
    session.commit()
    create_audit_log(
        session,
        action_type="story_suggestion_deleted",
        entity_type="story_suggestion",
        entity_id=str(suggestion_id),
        summary=f"Deleted story suggestion {suggestion_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"title": suggestion_title, "user_id": suggestion_user_id},
    )
