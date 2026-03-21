from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.schemas.recommendation_schema import RecommendationDebugResponse, RecommendationsResponse
from app.services.child_profile_service import get_child_profile_for_user
from app.services.parental_controls_service import filter_recommendation_like_items_by_parental_controls, resolve_parental_controls
from app.services.privacy_service import recommendation_personalization_allowed
from app.services.recommendation_service import (
    get_fallback_recommendations,
    get_more_like_this,
    get_personalized_recommendations_for_user,
)
from app.utils.dependencies import get_current_active_user, get_optional_current_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/me", response_model=RecommendationsResponse, summary="Get personalized recommendations for the current user")
def get_my_recommendations(
    age_band: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationsResponse:
    if not recommendation_personalization_allowed(session, user_id=current_user.id):
        child_profile = (
            get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)
            if child_profile_id is not None
            else None
        )
        controls = resolve_parental_controls(session, user=current_user, child_profile_id=child_profile_id)
        fallback_items = get_fallback_recommendations(
            session,
            language=child_profile.language if child_profile is not None else current_user.language,
            age_band=child_profile.age_band if child_profile is not None else age_band,
            limit=limit,
        )
        return RecommendationsResponse(items=filter_recommendation_like_items_by_parental_controls(fallback_items, controls=controls)[:limit])
    items, _evaluated_count = get_personalized_recommendations_for_user(
        session,
        user=current_user,
        child_profile_id=child_profile_id,
        age_band=age_band,
        limit=limit,
    )
    return RecommendationsResponse(items=items)


@router.get("/me/debug", response_model=RecommendationDebugResponse, summary="Debug recommendation scores for the current user")
def get_my_recommendations_debug(
    age_band: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationDebugResponse:
    if not recommendation_personalization_allowed(session, user_id=current_user.id):
        child_profile = (
            get_child_profile_for_user(session, user_id=current_user.id, child_profile_id=child_profile_id)
            if child_profile_id is not None
            else None
        )
        controls = resolve_parental_controls(session, user=current_user, child_profile_id=child_profile_id)
        fallback_items = get_fallback_recommendations(
            session,
            language=child_profile.language if child_profile is not None else current_user.language,
            age_band=child_profile.age_band if child_profile is not None else age_band,
            limit=limit,
        )
        return RecommendationDebugResponse(
            user_id=current_user.id,
            evaluated_count=0,
            items=filter_recommendation_like_items_by_parental_controls(fallback_items, controls=controls)[:limit],
        )
    items, evaluated_count = get_personalized_recommendations_for_user(
        session,
        user=current_user,
        child_profile_id=child_profile_id,
        age_band=age_band,
        limit=limit,
    )
    return RecommendationDebugResponse(user_id=current_user.id, evaluated_count=evaluated_count, items=items)


@router.get("/fallback", response_model=RecommendationsResponse, summary="Get fallback recommendations for guests or new users")
def get_fallback_recommendation_list(
    language: str | None = Query(default=None),
    age_band: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    session: Session = Depends(get_session),
) -> RecommendationsResponse:
    return RecommendationsResponse(items=get_fallback_recommendations(session, language=language, age_band=age_band, limit=limit))


@router.get(
    "/books/{book_id}/more-like-this",
    response_model=RecommendationsResponse,
    summary="Get books similar to the current story",
)
def get_more_like_this_books(
    book_id: int,
    user_context: bool = Query(default=True),
    child_profile_id: int | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=20),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> RecommendationsResponse:
    if child_profile_id is not None and current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required for child profile recommendations")
    items = get_more_like_this(
        session,
        book_id=book_id,
        user=current_user,
        child_profile_id=child_profile_id,
        user_context=user_context,
        limit=limit,
    )
    return RecommendationsResponse(items=items)
