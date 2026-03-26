from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Character, StoryIdea
from app.schemas.story_schema import (
    IdeaGenerationSummary,
    StoryIdeaBatchGenerateResponse,
    StoryIdeaCreate,
    StoryIdeaGenerateRequest,
    StoryIdeaRead,
    StoryIdeaSelectRequest,
    StoryIdeaUpdate,
)
from app.services.content_lane_service import validate_content_lane_key
from app.services.idea_generator import generate_story_idea_payloads
from app.services.story_suggestion_service import (
    build_story_suggestion_guidance_lines,
    list_story_suggestion_references,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(
    prefix="/story-ideas",
    tags=["story-ideas"],
    dependencies=[Depends(get_current_admin_user)],
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_story_idea_or_404(session: Session, idea_id: int) -> StoryIdea:
    story_idea = session.get(StoryIdea, idea_id)
    if story_idea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story idea not found")
    return story_idea


def _active_character_names(session: Session) -> list[str]:
    statement = select(Character.name).where(Character.is_active.is_(True)).order_by(Character.name)
    return list(session.exec(statement).all())


def _persist_story_idea(session: Session, story_idea: StoryIdea) -> StoryIdea:
    session.add(story_idea)
    session.commit()
    session.refresh(story_idea)
    return story_idea


@router.post(
    "/generate",
    response_model=StoryIdeaBatchGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a batch of structured story ideas",
)
def generate_story_ideas(
    payload: StoryIdeaGenerateRequest,
    session: Session = Depends(get_session),
) -> StoryIdeaBatchGenerateResponse:
    lane = validate_content_lane_key(
        session,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
    )
    available_characters = _active_character_names(session)
    # Exclude recent premises across all lanes so bedtime/adventure swaps still avoid repeats.
    recent_premises = session.exec(
        select(StoryIdea.premise).order_by(StoryIdea.created_at.desc()).limit(120),
    ).all()
    seen_keys: set[str] = set()
    exclude_set: set[str] = set()
    hint_lines: list[str] = []
    for p in recent_premises:
        s = str(p).strip()
        if not s:
            continue
        key = s.casefold()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        exclude_set.add(key)
        hint_lines.append(s[:240])
        if len(hint_lines) >= 35:
            break
    suggestion_guidance = tuple(
        build_story_suggestion_guidance_lines(
            list_story_suggestion_references(
                session,
                age_band=lane.age_band,
                limit=3,
            )
        )
    )
    batch = generate_story_idea_payloads(
        count=payload.count,
        age_band=lane.age_band,
        content_lane_key=lane.key,
        tone=payload.tone,
        include_characters=payload.include_characters,
        bedtime_only=payload.bedtime_only,
        available_characters=available_characters,
        exclude_premises=frozenset(exclude_set) if exclude_set else None,
        exclude_premise_hints=tuple(hint_lines) if hint_lines else None,
        editorial_guidance=suggestion_guidance or None,
    )

    created_ideas: list[StoryIdea] = []
    for item in batch.payloads:
        story_idea = StoryIdea(**item)
        session.add(story_idea)
        created_ideas.append(story_idea)

    session.commit()
    for story_idea in created_ideas:
        session.refresh(story_idea)

    return StoryIdeaBatchGenerateResponse(
        created_count=len(created_ideas),
        ideas=created_ideas,
        generation_summary=IdeaGenerationSummary(
            path=batch.path,
            excluded_recent_premise_count=batch.excluded_premise_count,
            llm_idea_count=batch.llm_idea_count,
            curated_idea_count=batch.curated_idea_count,
        ),
    )


@router.get("", response_model=list[StoryIdeaRead], summary="List story ideas")
def list_story_ideas(
    status: str | None = Query(default=None),
    age_band: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[StoryIdea]:
    statement = select(StoryIdea).order_by(StoryIdea.created_at.desc()).limit(limit)
    if status:
        statement = statement.where(StoryIdea.status == status)
    if age_band:
        statement = statement.where(StoryIdea.age_band == age_band)
    if content_lane_key:
        statement = statement.where(StoryIdea.content_lane_key == content_lane_key)
    return list(session.exec(statement).all())


@router.post(
    "",
    response_model=StoryIdeaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a story idea manually",
)
def create_story_idea(
    payload: StoryIdeaCreate,
    session: Session = Depends(get_session),
) -> StoryIdea:
    lane = validate_content_lane_key(
        session,
        age_band=payload.age_band,
        content_lane_key=payload.content_lane_key,
    )
    story_idea = StoryIdea.model_validate(
        payload.model_copy(update={"age_band": lane.age_band, "content_lane_key": lane.key})
    )
    return _persist_story_idea(session, story_idea)


@router.get("/{idea_id}", response_model=StoryIdeaRead, summary="Get a story idea by id")
def get_story_idea(idea_id: int, session: Session = Depends(get_session)) -> StoryIdea:
    return _get_story_idea_or_404(session, idea_id)


@router.patch(
    "/{idea_id}",
    response_model=StoryIdeaRead,
    summary="Partially update a story idea",
)
def update_story_idea(
    idea_id: int,
    payload: StoryIdeaUpdate,
    session: Session = Depends(get_session),
) -> StoryIdea:
    story_idea = _get_story_idea_or_404(session, idea_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "age_band" in update_data or "content_lane_key" in update_data:
        lane = validate_content_lane_key(
            session,
            age_band=update_data.get("age_band", story_idea.age_band),
            content_lane_key=update_data.get("content_lane_key", story_idea.content_lane_key),
        )
        update_data["age_band"] = lane.age_band
        update_data["content_lane_key"] = lane.key

    for field_name, value in update_data.items():
        setattr(story_idea, field_name, value)

    story_idea.updated_at = _utc_now()
    return _persist_story_idea(session, story_idea)


@router.delete(
    "/{idea_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a story idea",
)
def delete_story_idea(idea_id: int, session: Session = Depends(get_session)) -> Response:
    story_idea = _get_story_idea_or_404(session, idea_id)
    session.delete(story_idea)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{idea_id}/select",
    response_model=StoryIdeaRead,
    summary="Mark a story idea as selected, optionally assigning route (bedtime or adventure)",
)
def select_story_idea(
    idea_id: int,
    body: StoryIdeaSelectRequest | None = Body(default=None),
    session: Session = Depends(get_session),
) -> StoryIdea:
    story_idea = _get_story_idea_or_404(session, idea_id)
    if body and body.content_lane_key:
        lane = validate_content_lane_key(
            session,
            age_band=None,
            content_lane_key=body.content_lane_key,
        )
        story_idea.age_band = lane.age_band
        story_idea.content_lane_key = lane.key
    story_idea.status = "idea_selected"
    story_idea.updated_at = _utc_now()
    return _persist_story_idea(session, story_idea)


@router.post(
    "/{idea_id}/reject",
    response_model=StoryIdeaRead,
    summary="Mark a story idea as rejected",
)
def reject_story_idea(idea_id: int, session: Session = Depends(get_session)) -> StoryIdea:
    story_idea = _get_story_idea_or_404(session, idea_id)
    story_idea.status = "idea_rejected"
    story_idea.updated_at = _utc_now()
    return _persist_story_idea(session, story_idea)
