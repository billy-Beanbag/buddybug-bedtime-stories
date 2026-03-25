from app.models import Book, ChildProfile, StoryDraft
from app.services.story_writer import generate_story_draft_payload
from tests.utils import create_story_idea_for_lane, make_auth_headers


def _create_published_book(session, *, age_band: str, content_lane_key: str, language: str, title_suffix: str, audio_available: bool = False) -> Book:
    story_idea = create_story_idea_for_lane(
        session,
        age_band=age_band,
        content_lane_key=content_lane_key,
    )
    payload = generate_story_draft_payload(story_idea)
    story_draft = StoryDraft(
        story_idea_id=story_idea.id,
        title=f"{payload.title} {title_suffix}",
        content_lane_key=payload.content_lane_key,
        full_text=payload.full_text,
        summary=payload.summary,
        read_time_minutes=payload.read_time_minutes,
        review_status="approved_for_illustration",
        generation_source=payload.generation_source,
    )
    session.add(story_draft)
    session.commit()
    session.refresh(story_draft)

    book = Book(
        story_draft_id=story_draft.id,
        title=story_draft.title,
        age_band=age_band,
        content_lane_key=content_lane_key,
        language=language,
        published=True,
        publication_status="published",
        audio_available=audio_available,
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def test_authenticated_user_can_create_reading_plan(client, session, normal_user):
    child_profile = ChildProfile(user_id=normal_user.id, display_name="Daisy", age_band="3-7", language="es")
    session.add(child_profile)
    session.commit()
    session.refresh(child_profile)

    response = client.post(
        "/reading-plans/me",
        headers=make_auth_headers(normal_user),
        json={
            "child_profile_id": child_profile.id,
            "title": "Bedtime routine for Daisy",
            "plan_type": "bedtime",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Bedtime routine for Daisy"
    assert payload["child_profile_id"] == child_profile.id
    assert payload["preferred_age_band"] == "3-7"
    assert payload["preferred_language"] == "es"


def test_child_profile_ownership_is_validated_for_reading_plans(client, session, normal_user, premium_user):
    child_profile = ChildProfile(user_id=normal_user.id, display_name="Mila", age_band="3-7", language="en")
    session.add(child_profile)
    session.commit()
    session.refresh(child_profile)

    response = client.post(
        "/reading-plans/me",
        headers=make_auth_headers(premium_user),
        json={
            "child_profile_id": child_profile.id,
            "title": "Cozy reading",
            "plan_type": "custom",
        },
    )

    assert response.status_code == 404


def test_plan_detail_generates_upcoming_sessions(client, session, normal_user):
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Calm",
    )
    create_response = client.post(
        "/reading-plans/me",
        headers=make_auth_headers(normal_user),
        json={
            "title": "Three calm stories per week",
            "plan_type": "bedtime",
            "preferred_age_band": "3-7",
            "preferred_language": "en",
            "sessions_per_week": 3,
        },
    )
    plan_id = create_response.json()["id"]

    response = client.get(f"/reading-plans/me/{plan_id}", headers=make_auth_headers(normal_user))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["upcoming_sessions"]) == 3
    assert len({item["scheduled_date"] for item in payload["upcoming_sessions"]}) == 3
    assert payload["upcoming_sessions"][0]["suggested_book_id"] is not None


def test_plan_suggestions_respect_age_and_language_filters(client, session, normal_user):
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="es",
        title_suffix="Spanish",
        audio_available=True,
    )
    _create_published_book(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        language="en",
        title_suffix="Older",
        audio_available=True,
    )
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="English",
        audio_available=False,
    )
    create_response = client.post(
        "/reading-plans/me",
        headers=make_auth_headers(normal_user),
        json={
            "title": "Spanish story practice",
            "plan_type": "language_practice",
            "preferred_age_band": "3-7",
            "preferred_language": "es",
            "prefer_narration": True,
        },
    )
    plan_id = create_response.json()["id"]

    response = client.get(f"/reading-plans/me/{plan_id}/suggestions", headers=make_auth_headers(normal_user))

    assert response.status_code == 200
    items = response.json()["suggested_books"]
    assert items
    assert all(item["age_band"] == "3-7" for item in items)
    assert all(item["language"] == "es" for item in items)


def test_session_completion_works(client, session, normal_user):
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Complete",
    )
    create_response = client.post(
        "/reading-plans/me",
        headers=make_auth_headers(normal_user),
        json={
            "title": "Weekend family reading",
            "plan_type": "family_reading",
            "preferred_age_band": "3-7",
            "preferred_language": "en",
        },
    )
    plan_id = create_response.json()["id"]
    detail_response = client.get(f"/reading-plans/me/{plan_id}", headers=make_auth_headers(normal_user))
    session_id = detail_response.json()["upcoming_sessions"][0]["id"]

    response = client.post(
        f"/reading-plans/me/{plan_id}/sessions/{session_id}/complete",
        headers=make_auth_headers(normal_user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["completed"] is True
    assert payload["completed_at"] is not None


def test_user_cannot_access_another_users_plan(client, normal_user, premium_user):
    create_response = client.post(
        "/reading-plans/me",
        headers=make_auth_headers(normal_user),
        json={
            "title": "Narrated story nights",
            "plan_type": "narrated",
        },
    )
    plan_id = create_response.json()["id"]

    response = client.get(f"/reading-plans/me/{plan_id}", headers=make_auth_headers(premium_user))

    assert response.status_code == 404
