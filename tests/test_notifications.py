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


def test_default_notification_preferences_auto_create(client, user_token_headers):
    response = client.get("/notifications/preferences/me", headers=user_token_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["enable_in_app"] is True
    assert payload["enable_bedtime_reminders"] is True
    assert payload["enable_weekly_digest"] is False


def test_user_can_update_notification_preferences(client, user_token_headers):
    response = client.patch(
        "/notifications/preferences/me",
        headers=user_token_headers,
        json={
            "enable_new_story_alerts": False,
            "enable_email_placeholder": True,
            "quiet_hours_start": "20:00",
            "quiet_hours_end": "07:00",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["enable_new_story_alerts"] is False
    assert payload["enable_email_placeholder"] is True
    assert payload["quiet_hours_start"] == "20:00"


def test_user_can_only_list_their_own_notifications(client, admin_token_headers, user_token_headers, normal_user, premium_user):
    client.post(
        f"/admin/notifications/users/{normal_user.id}/create",
        headers=admin_token_headers,
        json={
            "notification_type": "saved_story_ready",
            "delivery_channel": "in_app",
            "title": "Your saved story is ready",
            "body": "A story is ready for tonight.",
        },
    )
    client.post(
        f"/admin/notifications/users/{premium_user.id}/create",
        headers=admin_token_headers,
        json={
            "notification_type": "premium_expiring_soon",
            "delivery_channel": "in_app",
            "title": "Premium renews soon",
            "body": "Check your billing details.",
        },
    )

    response = client.get("/notifications/me", headers=user_token_headers)

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Your saved story is ready"


def test_mark_all_read_works(client, admin_token_headers, user_token_headers, normal_user):
    for index in range(2):
        client.post(
            f"/admin/notifications/users/{normal_user.id}/create",
            headers=admin_token_headers,
            json={
                "notification_type": "saved_story_ready",
                "delivery_channel": "in_app",
                "title": f"Saved story {index}",
                "body": "Ready for tonight.",
            },
        )

    mark_response = client.post("/notifications/me/mark-all-read", headers=user_token_headers)
    unread_response = client.get("/notifications/me?unread_only=true", headers=user_token_headers)

    assert mark_response.status_code == 200
    assert mark_response.json()["updated_count"] == 2
    assert unread_response.status_code == 200
    assert unread_response.json()["items"] == []


def test_daily_story_suggestion_can_be_generated(client, session, user_token_headers):
    bedtime_book = _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Tonight",
    )

    response = client.get("/notifications/me/daily-story", headers=user_token_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["suggestion"] is not None
    assert payload["suggestion"]["book_id"] == bedtime_book.id
    assert payload["book"]["book_id"] == bedtime_book.id


def test_child_profile_id_ownership_is_validated_for_daily_story(client, normal_user, premium_user):
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Mia", "age_band": "3-7", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    response = client.get(
        f"/notifications/me/daily-story?child_profile_id={child_profile_id}",
        headers=make_auth_headers(premium_user),
    )

    assert response.status_code == 404


def test_daily_story_respects_age_band_and_parental_controls(client, session, normal_user):
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Younger",
    )
    _create_published_book(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        language="fr",
        title_suffix="Older",
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
        json={"allow_8_12_content": False, "max_allowed_age_band": "3-7"},
    )
    assert controls_response.status_code == 200

    response = client.get(
        f"/notifications/me/daily-story?child_profile_id={child_profile_id}",
        headers=make_auth_headers(normal_user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["suggestion"] is None
    assert payload["book"] is None
