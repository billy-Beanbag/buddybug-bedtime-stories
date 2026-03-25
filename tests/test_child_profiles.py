from app.models import Book, ReadingProgress, StoryDraft, UserStoryFeedback
from app.services.story_writer import generate_story_draft_payload
from tests.utils import create_story_idea_for_lane, make_auth_headers


def _create_published_book(session, *, age_band: str, content_lane_key: str, language: str, title_suffix: str) -> Book:
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
        audio_available=False,
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def test_authenticated_user_can_create_child_profile(client, user_token_headers):
    response = client.post(
        "/child-profiles",
        headers=user_token_headers,
        json={"display_name": "Mia", "age_band": "3-7", "language": "en"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["child_profile"]["display_name"] == "Mia"
    assert payload["child_profile"]["content_lane_key"] == "bedtime_3_7"
    assert payload["reading_profile"]["child_profile_id"] == payload["child_profile"]["id"]


def test_user_can_only_access_their_own_child_profiles(client, session, normal_user, premium_user):
    create_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Theo", "age_band": "8-12", "language": "fr"},
    )
    child_profile_id = create_response.json()["child_profile"]["id"]

    response = client.get(f"/child-profiles/{child_profile_id}", headers=make_auth_headers(premium_user))

    assert response.status_code == 404


def test_child_age_band_resolves_correct_default_lane(client, user_token_headers):
    response = client.post(
        "/child-profiles",
        headers=user_token_headers,
        json={"display_name": "Ava", "age_band": "8-12", "language": "en"},
    )

    assert response.status_code == 201
    assert response.json()["child_profile"]["content_lane_key"] == "story_adventures_3_7"


def test_reading_progress_can_be_stored_with_child_profile_id(client, session, demo_published_book, normal_user):
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Luca", "age_band": "3-7", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    response = client.post(
        "/reader/progress",
        headers=make_auth_headers(normal_user),
        json={
            "reader_identifier": f"user:{normal_user.id}",
            "book_id": demo_published_book.id,
            "child_profile_id": child_profile_id,
            "current_page_number": 1,
            "completed": False,
        },
    )

    assert response.status_code == 200
    progress = session.get(ReadingProgress, response.json()["id"])
    assert progress is not None
    assert progress.child_profile_id == child_profile_id


def test_feedback_can_be_stored_with_child_profile_id(client, session, normal_user):
    book = _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Feedback",
    )
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Sage", "age_band": "3-7", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    response = client.post(
        f"/feedback/me/books/{book.id}",
        headers=make_auth_headers(normal_user),
        json={
            "child_profile_id": child_profile_id,
            "liked": True,
            "rating": 5,
            "completed": True,
            "replayed": False,
        },
    )

    assert response.status_code == 200
    feedback_id = response.json()["feedback"]["id"]
    feedback = session.get(UserStoryFeedback, feedback_id)
    assert feedback is not None
    assert feedback.child_profile_id == child_profile_id


def test_child_recommendation_request_respects_age_band_and_language(client, session, normal_user):
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Younger",
    )
    fr_book = _create_published_book(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        language="fr",
        title_suffix="French",
    )
    _create_published_book(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        language="en",
        title_suffix="English",
    )
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Noah", "age_band": "8-12", "language": "fr"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]
    controls_response = client.patch(
        "/parental-controls/me",
        headers=make_auth_headers(normal_user),
        json={
            "allow_8_12_content": True,
            "max_allowed_age_band": "8-12",
            "bedtime_mode_default": False,
            "hide_adventure_content_at_bedtime": False,
        },
    )
    assert controls_response.status_code == 200

    response = client.get(
        f"/recommendations/me?child_profile_id={child_profile_id}",
        headers=make_auth_headers(normal_user),
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["age_band"] == "8-12" for item in items)
    assert items[0]["book_id"] == fr_book.id
