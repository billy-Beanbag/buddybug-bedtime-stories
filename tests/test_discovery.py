from sqlmodel import select

from app.models import Book, BookDiscoveryMetadata, StoryDraft
from app.services.story_writer import generate_story_draft_payload
from tests.utils import create_story_idea_for_lane, make_auth_headers


def _create_book(session, *, age_band: str, lane_key: str, language: str, title_suffix: str, published: bool) -> Book:
    story_idea = create_story_idea_for_lane(session, age_band=age_band, content_lane_key=lane_key)
    payload = generate_story_draft_payload(story_idea)
    draft = StoryDraft(
        story_idea_id=story_idea.id,
        title=f"{payload.title} {title_suffix}",
        age_band=age_band,
        language=language,
        content_lane_key=lane_key,
        full_text=payload.full_text,
        summary=payload.summary,
        read_time_minutes=payload.read_time_minutes,
        review_status="approved_for_illustration",
        generation_source=payload.generation_source,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    book = Book(
        story_draft_id=draft.id,
        title=draft.title,
        age_band=age_band,
        content_lane_key=lane_key,
        language=language,
        published=published,
        publication_status="published" if published else "ready",
        audio_available=False,
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def test_published_books_appear_in_search(client, session):
    book = _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="Moon", published=True)

    response = client.get("/discovery/search?q=moon")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["book_id"] == book.id


def test_unpublished_books_do_not_appear(client, session):
    _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="Hidden", published=False)

    response = client.get("/discovery/search?q=hidden")

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_language_filter_works(client, session):
    english = _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="English", published=True)
    spanish = _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="es", title_suffix="Spanish", published=True)

    response = client.get("/discovery/search?language=es")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["book_id"] for item in items] == [spanish.id]
    assert english.id not in [item["book_id"] for item in items]


def test_age_band_and_content_lane_filter_works(client, session):
    younger = _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="Younger", published=True)
    older = _create_book(session, age_band="8-12", lane_key="story_adventures_3_7", language="en", title_suffix="Older", published=True)

    response = client.get("/discovery/search?age_band=8-12&content_lane_key=story_adventures_3_7")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["book_id"] for item in items] == [older.id]
    assert younger.id not in [item["book_id"] for item in items]


def test_collection_detail_returns_only_included_books(client, session, editor_token_headers):
    first = _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="First", published=True)
    second = _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="Second", published=True)
    collection_response = client.post(
        "/admin/discovery/collections",
        headers=editor_token_headers,
        json={"key": "test_collection", "title": "Test Collection"},
    )
    collection_id = collection_response.json()["id"]
    client.post(
        f"/admin/discovery/collections/{collection_id}/items",
        headers=editor_token_headers,
        json={"book_id": second.id, "position": 2},
    )

    response = client.get("/discovery/collections/test_collection")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["book_id"] == second.id
    assert first.id not in [item["book_id"] for item in items]


def test_parental_controls_filter_out_disallowed_books(client, session, normal_user):
    _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="Calm", published=True)
    older = _create_book(session, age_band="8-12", lane_key="story_adventures_3_7", language="en", title_suffix="Adventure", published=True)
    child_response = client.post(
        "/child-profiles",
        headers=make_auth_headers(normal_user),
        json={"display_name": "Mia", "age_band": "8-12", "language": "en"},
    )
    child_profile_id = child_response.json()["child_profile"]["id"]
    client.patch(
        "/parental-controls/me",
        headers=make_auth_headers(normal_user),
        json={"allow_8_12_content": False, "max_allowed_age_band": "3-7"},
    )

    response = client.get(
        f"/discovery/search?child_profile_id={child_profile_id}",
        headers=make_auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert older.id not in [item["book_id"] for item in response.json()["items"]]


def test_rebuilding_metadata_creates_and_updates_row(client, session, editor_token_headers):
    book = _create_book(session, age_band="3-7", lane_key="bedtime_3_7", language="en", title_suffix="Metadata", published=True)

    rebuild_response = client.post(f"/admin/discovery/books/{book.id}/rebuild", headers=editor_token_headers)
    patch_response = client.patch(
        f"/admin/discovery/books/{book.id}/metadata",
        headers=editor_token_headers,
        json={"is_featured": True, "theme_tags": "moonlight, bedtime"},
    )

    assert rebuild_response.status_code == 200
    assert patch_response.status_code == 200
    metadata = session.exec(select(BookDiscoveryMetadata).where(BookDiscoveryMetadata.book_id == book.id)).first()
    assert metadata is not None
    assert metadata.is_featured is True
    assert metadata.theme_tags == "moonlight, bedtime"
