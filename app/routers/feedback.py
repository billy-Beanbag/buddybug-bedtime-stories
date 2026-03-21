from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, UserStoryFeedback, UserStoryProfile
from app.schemas.feedback_schema import (
    FeedbackSummaryResponse,
    UserStoryFeedbackCreate,
    UserStoryFeedbackRead,
    UserStoryFeedbackUpdate,
    UserStoryProfileRead,
)
from app.services.analytics_service import track_event_safe
from app.services.feedback_service import (
    create_or_update_feedback,
    get_feedback_for_user_and_book,
    list_feedback_for_user,
    rebuild_user_story_profile,
    update_feedback,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _get_user_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _get_or_create_profile(session: Session, user_id: int) -> UserStoryProfile:
    _get_user_or_404(session, user_id)
    profile = session.exec(select(UserStoryProfile).where(UserStoryProfile.user_id == user_id)).first()
    if profile is None:
        profile = rebuild_user_story_profile(session, user_id=user_id)
    return profile


@router.get("/me", response_model=list[UserStoryFeedbackRead], summary="List feedback for the current user")
def get_my_feedback(
    liked: bool | None = Query(default=None),
    completed: bool | None = Query(default=None),
    replayed: bool | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[UserStoryFeedback]:
    return list_feedback_for_user(
        session,
        user_id=current_user.id,
        liked=liked,
        completed=completed,
        replayed=replayed,
        child_profile_id=child_profile_id,
        limit=limit,
    )


@router.get(
    "/me/books/{book_id}",
    response_model=UserStoryFeedbackRead,
    summary="Get the current user's feedback for one book",
)
def get_my_feedback_for_book(
    book_id: int,
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserStoryFeedback:
    feedback = get_feedback_for_user_and_book(
        session,
        user_id=current_user.id,
        book_id=book_id,
        child_profile_id=child_profile_id,
    )
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    return feedback


@router.post(
    "/me/books/{book_id}",
    response_model=FeedbackSummaryResponse,
    summary="Create or replace feedback for the current user and one book",
)
def create_my_feedback_for_book(
    book_id: int,
    payload: UserStoryFeedbackUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> FeedbackSummaryResponse:
    feedback, profile = create_or_update_feedback(
        session,
        user_id=current_user.id,
        book_id=book_id,
        child_profile_id=payload.child_profile_id,
        liked=payload.liked,
        rating=payload.rating,
        completed=payload.completed or False,
        replayed=payload.replayed or False,
        preferred_character=payload.preferred_character,
        preferred_style=payload.preferred_style,
        preferred_tone=payload.preferred_tone,
        feedback_notes=payload.feedback_notes,
    )
    track_event_safe(
        session,
        event_name="feedback_submitted",
        user=current_user,
        child_profile_id=payload.child_profile_id,
        book_id=book_id,
        metadata={
            "source": "feedback_create",
            "rating": feedback.rating,
            "liked": feedback.liked,
            "completed": feedback.completed,
            "replayed": feedback.replayed,
        },
    )
    return FeedbackSummaryResponse(feedback=feedback, profile=profile)


@router.patch(
    "/me/books/{book_id}",
    response_model=FeedbackSummaryResponse,
    summary="Partially update feedback for the current user and one book",
)
def patch_my_feedback_for_book(
    book_id: int,
    payload: UserStoryFeedbackUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> FeedbackSummaryResponse:
    feedback = get_feedback_for_user_and_book(
        session,
        user_id=current_user.id,
        book_id=book_id,
        child_profile_id=payload.child_profile_id,
    )
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    feedback, profile = update_feedback(
        session,
        feedback=feedback,
        liked=payload.liked,
        rating=payload.rating,
        completed=payload.completed,
        replayed=payload.replayed,
        preferred_character=payload.preferred_character,
        preferred_style=payload.preferred_style,
        preferred_tone=payload.preferred_tone,
        feedback_notes=payload.feedback_notes,
    )
    track_event_safe(
        session,
        event_name="feedback_submitted",
        user=current_user,
        child_profile_id=feedback.child_profile_id,
        book_id=book_id,
        metadata={
            "source": "feedback_update",
            "rating": feedback.rating,
            "liked": feedback.liked,
            "completed": feedback.completed,
            "replayed": feedback.replayed,
        },
    )
    return FeedbackSummaryResponse(feedback=feedback, profile=profile)


@router.get("/me/profile", response_model=UserStoryProfileRead, summary="Get the current user's taste profile")
def get_my_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserStoryProfile:
    return _get_or_create_profile(session, current_user.id)


@router.post(
    "/me/profile/rebuild",
    response_model=UserStoryProfileRead,
    summary="Rebuild the current user's taste profile",
)
def rebuild_my_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UserStoryProfile:
    return rebuild_user_story_profile(session, user_id=current_user.id)


@router.get(
    "/users/{user_id}",
    response_model=list[UserStoryFeedbackRead],
    summary="List feedback for one user (internal authenticated read)",
)
def get_feedback_for_user_id(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_active_user),
) -> list[UserStoryFeedback]:
    return list_feedback_for_user(session, user_id=user_id, limit=300)


@router.get(
    "/users/{user_id}/profile",
    response_model=UserStoryProfileRead,
    summary="Get a user's aggregate story profile (internal authenticated read)",
)
def get_profile_for_user_id(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_active_user),
) -> UserStoryProfile:
    return _get_or_create_profile(session, user_id)
