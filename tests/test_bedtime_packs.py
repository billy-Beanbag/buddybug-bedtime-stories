from app.models import Book, StoryDraft
from app.services.story_writer import generate_story_draft_payload
from tests.utils import create_story_idea_for_lane, make_auth_headers


def _create_published_book(
    session,
    *,
    age_band: str,
    content_lane_key: str,
    language: str,
    title_suffix: str,
    audio_available: bool = False,
) -> Book:
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


def test_latest_pack_generates_when_missing(client, session, normal_user):
    for index in range(3):
        _create_published_book(
            session,
            age_band="3-7",
            content_lane_key="bedtime_3_7",
            language="en",
            title_suffix=f"Night {index}",
            audio_available=index == 0,
        )

    response = client.get("/bedtime-packs/me/latest", headers=make_auth_headers(normal_user))

    assert response.status_code == 200
    payload = response.json()
    assert payload["pack"]["pack_type"] == "nightly"
    assert 2 <= len(payload["items"]) <= 4


def test_child_profile_ownership_is_validated_for_bedtime_packs(client, normal_user, premium_user):
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Daisy", "age_band": "3-7", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]

    response = client.get(
        f"/bedtime-packs/me/latest?child_profile_id={child_profile_id}",
        headers=make_auth_headers(premium_user),
    )

    assert response.status_code == 404


def test_generated_packs_contain_two_to_four_ordered_items(client, session, normal_user):
    for index in range(4):
        _create_published_book(
            session,
            age_band="3-7",
            content_lane_key="bedtime_3_7",
            language="en",
            title_suffix=f"Ordered {index}",
            audio_available=index % 2 == 0,
        )

    response = client.post(
        "/bedtime-packs/me/generate",
        headers=make_auth_headers(normal_user),
        json={"pack_type": "weekend", "prefer_narration": True},
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert 2 <= len(items) <= 4
    assert [item["position"] for item in items] == list(range(1, len(items) + 1))


def test_parental_controls_and_age_band_filters_are_respected(client, session, normal_user):
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Allowed",
    )
    _create_published_book(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        title_suffix="Allowed Two",
    )
    blocked_book = _create_published_book(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        language="en",
        title_suffix="Blocked",
    )
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Noah", "age_band": "8-12", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]
    client.patch(
        "/parental-controls/me",
        headers=make_auth_headers(normal_user),
        json={"allow_8_12_content": False, "max_allowed_age_band": "3-7", "hide_adventure_content_at_bedtime": True},
    )

    response = client.post(
        "/bedtime-packs/me/generate",
        headers=make_auth_headers(normal_user),
        json={"child_profile_id": child_profile_id},
    )

    assert response.status_code == 200
    assert all(item["book_id"] != blocked_book.id for item in response.json()["items"])


def test_item_status_updates_work(client, session, normal_user):
    for index in range(3):
        _create_published_book(
            session,
            age_band="3-7",
            content_lane_key="bedtime_3_7",
            language="en",
            title_suffix=f"Status {index}",
        )
    pack_response = client.get("/bedtime-packs/me/latest", headers=make_auth_headers(normal_user))
    pack_id = pack_response.json()["pack"]["id"]
    item_id = pack_response.json()["items"][0]["id"]

    response = client.patch(
        f"/bedtime-packs/me/{pack_id}/items/{item_id}",
        headers=make_auth_headers(normal_user),
        json={"completion_status": "completed"},
    )

    assert response.status_code == 200
    assert response.json()["completion_status"] == "completed"


def test_repeated_latest_fetch_reuses_current_pack_for_same_day(client, session, normal_user):
    for index in range(3):
        _create_published_book(
            session,
            age_band="3-7",
            content_lane_key="bedtime_3_7",
            language="en",
            title_suffix=f"Reuse {index}",
        )

    first = client.get("/bedtime-packs/me/latest", headers=make_auth_headers(normal_user))
    second = client.get("/bedtime-packs/me/latest", headers=make_auth_headers(normal_user))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["pack"]["id"] == second.json()["pack"]["id"]
