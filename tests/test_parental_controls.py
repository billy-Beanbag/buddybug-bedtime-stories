from app.models import Book, StoryDraft
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


def test_default_parent_settings_are_auto_created(client, user_token_headers):
    response = client.get("/parental-controls/me", headers=user_token_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["bedtime_mode_default"] is True
    assert payload["allow_audio_autoplay"] is False
    assert payload["max_allowed_age_band"] == "3-7"


def test_parent_can_update_settings(client, user_token_headers):
    response = client.patch(
        "/parental-controls/me",
        headers=user_token_headers,
        json={
            "allow_8_12_content": True,
            "max_allowed_age_band": "8-12",
            "allow_audio_autoplay": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["allow_8_12_content"] is True
    assert payload["max_allowed_age_band"] == "8-12"
    assert payload["allow_audio_autoplay"] is True


def test_child_override_can_be_created_only_for_owned_child_profile(client, normal_user, premium_user):
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Milo", "age_band": "3-7", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    response = client.patch(
        f"/parental-controls/children/{child_profile_id}",
        headers=make_auth_headers(premium_user),
        json={"allow_audio_autoplay": True},
    )

    assert response.status_code == 404


def test_resolved_controls_inherit_from_parent_and_child_override(client, normal_user):
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Luna", "age_band": "3-7", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    client.patch(
        "/parental-controls/me",
        headers=make_auth_headers(normal_user),
        json={
            "bedtime_mode_default": True,
            "allow_audio_autoplay": False,
            "allow_8_12_content": False,
            "max_allowed_age_band": "3-7",
        },
    )
    client.patch(
        f"/parental-controls/children/{child_profile_id}",
        headers=make_auth_headers(normal_user),
        json={"allow_audio_autoplay": True},
    )

    response = client.get(
        f"/parental-controls/resolved?child_profile_id={child_profile_id}",
        headers=make_auth_headers(normal_user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["bedtime_mode_enabled"] is True
    assert payload["allow_audio_autoplay"] is True
    assert payload["allow_8_12_content"] is False
    assert payload["max_allowed_age_band"] == "3-7"


def test_library_and_recommendation_filtering_respects_controls(client, session, normal_user):
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Bedtime",
    )
    blocked_book = _create_published_book(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        language="en",
        title_suffix="Adventure",
    )
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Ivy", "age_band": "8-12", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    client.patch(
        "/parental-controls/me",
        headers=make_auth_headers(normal_user),
        json={
            "allow_8_12_content": False,
            "max_allowed_age_band": "3-7",
            "hide_adventure_content_at_bedtime": True,
        },
    )

    reader_response = client.get(
        f"/reader/books?child_profile_id={child_profile_id}",
        headers=make_auth_headers(normal_user),
    )
    recommendation_response = client.get(
        f"/recommendations/me?child_profile_id={child_profile_id}",
        headers=make_auth_headers(normal_user),
    )

    assert reader_response.status_code == 200
    assert all(item["book_id"] != blocked_book.id for item in reader_response.json())
    assert recommendation_response.status_code == 200
    assert all(item["book_id"] != blocked_book.id for item in recommendation_response.json()["items"])


def test_audio_autoplay_restriction_resolves_correctly(client, normal_user):
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Nora", "age_band": "3-7", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    client.patch(
        "/parental-controls/me",
        headers=make_auth_headers(normal_user),
        json={"allow_audio_autoplay": False},
    )

    response = client.get(
        f"/parental-controls/resolved?child_profile_id={child_profile_id}",
        headers=make_auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert response.json()["allow_audio_autoplay"] is False
