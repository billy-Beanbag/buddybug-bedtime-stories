import json

import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Book, ClassicAdaptationDraft, ClassicSource, Illustration, StoryPage
from app.services.illustration_generator import approve_illustration
from tests.fixtures_classics import (
    GOLDILOCKS_TEST_TITLE,
    build_goldilocks_classic_payload,
    build_little_red_classic_payload,
    create_goldilocks_classic_source,
)
from tests.utils import create_demo_pipeline


def _create_import(client, headers: dict[str, str], *, payload: dict | None = None):
    return client.post("/classics/sources", json=payload or build_goldilocks_classic_payload(), headers=headers)


def _adapt_import(client, source_id: int, headers: dict[str, str], **overrides):
    payload = {
        "age_band": "3-7",
        "content_lane_key": "bedtime_3_7",
        "language": "en",
        "adaptation_intensity": "light",
        "min_pages": 5,
        "max_pages": 6,
    }
    payload.update(overrides)
    return client.post(f"/classics/sources/{source_id}/adapt", json=payload, headers=headers)


def test_classics_routes_require_editor_access(client, editor_token_headers, user_token_headers):
    unauthenticated = client.get("/classics/sources")
    assert unauthenticated.status_code == 401

    normal_user = client.get("/classics/sources", headers=user_token_headers)
    assert normal_user.status_code == 403

    editor_user = client.get("/classics/sources", headers=editor_token_headers)
    assert editor_user.status_code == 200


def test_classic_import_requires_fields_detects_duplicates_and_stays_internal(
    client,
    editor_token_headers,
    user_token_headers,
):
    created = _create_import(client, editor_token_headers)
    assert created.status_code == 201
    payload = created.json()
    assert payload["title"] == GOLDILOCKS_TEST_TITLE
    assert payload["public_domain_verified"] is True
    assert payload["import_status"] == "imported"

    missing_fields = client.post("/classics/sources", json={"title": "Goldilocks"}, headers=editor_token_headers)
    assert missing_fields.status_code == 422

    duplicate = _create_import(client, editor_token_headers)
    assert duplicate.status_code == 400
    assert "already exists" in duplicate.json()["detail"]

    blocked_for_normal_user = client.get(f"/classics/sources/{payload['id']}", headers=user_token_headers)
    assert blocked_for_normal_user.status_code == 403

    public_list = client.get("/reader/books")
    assert public_list.status_code == 200
    assert all(book["title"] != GOLDILOCKS_TEST_TITLE for book in public_list.json())


@pytest.mark.parametrize(
    ("payload_builder", "expected_title"),
    [
        (build_goldilocks_classic_payload, GOLDILOCKS_TEST_TITLE),
        (build_little_red_classic_payload, "Little Red Riding Hood"),
    ],
)
def test_controlled_classic_fixtures_can_be_imported_and_adapted(
    client,
    editor_token_headers,
    payload_builder,
    expected_title: str,
):
    import_response = _create_import(client, editor_token_headers, payload=payload_builder())
    assert import_response.status_code == 201
    classic_source_id = import_response.json()["id"]

    adapt_response = _adapt_import(client, classic_source_id, editor_token_headers)
    assert adapt_response.status_code == 201
    data = adapt_response.json()

    assert data["source"]["title"] == expected_title
    assert data["adaptation"]["adapted_title"]
    assert data["adaptation"]["adapted_text"]
    assert data["adaptation"]["validation_status"] in {"accepted", "accepted_with_warnings"}
    assert data["adaptation"]["scene_seed_notes_json"]


def test_classic_adaptation_generates_internal_draft_bundle_and_preview_stays_hidden(
    client,
    session: Session,
    editor_user,
    editor_token_headers,
):
    classic_source = create_goldilocks_classic_source(session, current_user=editor_user)

    response = _adapt_import(client, classic_source.id, editor_token_headers)
    assert response.status_code == 201
    data = response.json()

    assert data["adaptation"]["adapted_title"]
    assert data["adaptation"]["adapted_text"]
    assert data["adaptation"]["cameo_insertions_summary"]
    assert data["adaptation"]["adaptation_notes"]
    assert data["adaptation"]["scene_seed_notes_json"]
    assert data["adaptation"]["validation_status"] in {"accepted", "accepted_with_warnings"}
    assert data["adaptation"]["review_status"] == "pending"
    assert data["source"]["import_status"] == "drafted"
    assert len(data["story_pages"]) >= 2

    scene_seed_notes = json.loads(data["adaptation"]["scene_seed_notes_json"])
    assert len(scene_seed_notes) >= 2
    assert any(not note["featuredCharacters"] for note in scene_seed_notes)
    assert all("setting" in note and "keyVisualAction" in note for note in scene_seed_notes)
    assert any("Classic story illustration mode:" in page["illustration_prompt"] for page in data["story_pages"])

    preview_book_id = data["adaptation"]["preview_book_id"]
    reader_preview = client.get(f"/reader/books/{preview_book_id}")
    assert reader_preview.status_code == 404


def test_classic_validation_rejected_draft_cannot_be_approved(client, session: Session, editor_user, editor_token_headers):
    classic_source = create_goldilocks_classic_source(session, current_user=editor_user)
    adapt_response = _adapt_import(client, classic_source.id, editor_token_headers)
    draft_id = adapt_response.json()["adaptation"]["id"]

    patch_response = client.patch(
        f"/classics/drafts/{draft_id}",
        json={"validation_status": "rejected"},
        headers=editor_token_headers,
    )
    assert patch_response.status_code == 200

    approve_response = client.post(f"/classics/drafts/{draft_id}/approve", headers=editor_token_headers)
    assert approve_response.status_code == 400
    assert "failed validation" in approve_response.json()["detail"]


def test_classic_illustration_generation_creates_assets_and_failure_does_not_publish(
    client,
    session: Session,
    editor_user,
    editor_token_headers,
    monkeypatch: pytest.MonkeyPatch,
):
    classic_source = create_goldilocks_classic_source(session, current_user=editor_user)
    adapt_response = _adapt_import(client, classic_source.id, editor_token_headers)
    draft_id = adapt_response.json()["adaptation"]["id"]
    story_draft_id = adapt_response.json()["adaptation"]["story_draft_id"]

    response = client.post(f"/classics/drafts/{draft_id}/generate-illustrations", headers=editor_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["generated_count"] >= 2

    story_pages = list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft_id)).all())
    illustrations = list(
        session.exec(
            select(Illustration)
            .where(Illustration.story_page_id.in_([page.id for page in story_pages]))
            .order_by(Illustration.story_page_id, Illustration.version_number)
        ).all()
    )
    assert len(illustrations) == len(story_pages)

    draft = session.get(ClassicAdaptationDraft, draft_id)
    source = session.get(ClassicSource, classic_source.id)
    assert draft is not None and draft.illustration_status == "illustrated"
    assert source is not None and source.import_status == "illustrated"

    public_list = client.get("/reader/books")
    assert all(book["title"] != GOLDILOCKS_TEST_TITLE for book in public_list.json())

    def raise_mock_failure(*args, **kwargs):
        raise HTTPException(status_code=502, detail="Mock illustration failure")

    monkeypatch.setattr("app.services.classics_service.generate_illustration_asset", raise_mock_failure)
    failure_response = client.post(f"/classics/drafts/{draft_id}/generate-illustrations", headers=editor_token_headers)
    assert failure_response.status_code == 502

    unpublished_books = list(
        session.exec(select(Book).where(Book.classic_source_id == classic_source.id, Book.published.is_(True))).all()
    )
    assert unpublished_books == []


def test_classic_publish_requires_approval_and_published_classic_enters_public_library(
    client,
    session: Session,
    editor_user,
    editor_token_headers,
):
    classic_source = create_goldilocks_classic_source(session, current_user=editor_user)
    adapt_response = _adapt_import(client, classic_source.id, editor_token_headers)
    draft_id = adapt_response.json()["adaptation"]["id"]
    story_draft_id = adapt_response.json()["adaptation"]["story_draft_id"]

    blocked_publish = client.post(f"/classics/drafts/{draft_id}/publish", headers=editor_token_headers)
    assert blocked_publish.status_code == 400
    assert "must be approved" in blocked_publish.json()["detail"]

    missing_draft_illustrations = client.post("/classics/drafts/999999/generate-illustrations", headers=editor_token_headers)
    assert missing_draft_illustrations.status_code == 404

    client.post(f"/classics/drafts/{draft_id}/generate-illustrations", headers=editor_token_headers)

    story_pages = list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft_id)).all())
    illustrations = list(
        session.exec(select(Illustration).where(Illustration.story_page_id.in_([page.id for page in story_pages]))).all()
    )
    for illustration in illustrations:
        approve_illustration(session, illustration)

    approve_response = client.post(f"/classics/drafts/{draft_id}/approve", headers=editor_token_headers)
    assert approve_response.status_code == 200
    assert approve_response.json()["review_status"] == "approved"

    publish_response = client.post(f"/classics/drafts/{draft_id}/publish", headers=editor_token_headers)
    assert publish_response.status_code == 200
    published = publish_response.json()
    assert published["book"]["is_classic"] is True
    assert published["book"]["published"] is True
    assert published["adaptation"]["illustration_status"] == "published"
    assert published["source"]["import_status"] == "published"

    reader_full = client.get("/reader/books")
    assert reader_full.status_code == 200
    full_books = reader_full.json()
    classic_entry = next(book for book in full_books if book["title"] == GOLDILOCKS_TEST_TITLE)
    assert classic_entry["is_classic"] is True
    assert "review_status" not in classic_entry
    assert "import_status" not in classic_entry
    assert "source_text" not in classic_entry

    reader_classics = client.get("/reader/books", params={"is_classic": "true"})
    classic_titles = [book["title"] for book in reader_classics.json()]
    assert GOLDILOCKS_TEST_TITLE in classic_titles

    reader_non_classics = client.get("/reader/books", params={"is_classic": "false"})
    assert GOLDILOCKS_TEST_TITLE not in [book["title"] for book in reader_non_classics.json()]

    reader_detail = client.get(f"/reader/books/{published['book']['id']}")
    assert reader_detail.status_code == 200
    detail = reader_detail.json()
    assert detail["is_classic"] is True
    assert "source_url" not in detail
    assert "source_text" not in detail


def test_classic_filter_does_not_affect_non_classic_library_entries(
    client,
    session: Session,
    editor_user,
    editor_token_headers,
):
    create_demo_pipeline(session, publish=True, with_audio=False)
    classic_source = create_goldilocks_classic_source(session, current_user=editor_user)
    adapt_response = _adapt_import(client, classic_source.id, editor_token_headers)
    draft_id = adapt_response.json()["adaptation"]["id"]
    story_draft_id = adapt_response.json()["adaptation"]["story_draft_id"]
    client.post(f"/classics/drafts/{draft_id}/generate-illustrations", headers=editor_token_headers)
    story_pages = list(session.exec(select(StoryPage).where(StoryPage.story_draft_id == story_draft_id)).all())
    for illustration in session.exec(select(Illustration).where(Illustration.story_page_id.in_([page.id for page in story_pages]))).all():
        approve_illustration(session, illustration)
    client.post(f"/classics/drafts/{draft_id}/approve", headers=editor_token_headers)
    client.post(f"/classics/drafts/{draft_id}/publish", headers=editor_token_headers)

    full_listing = client.get("/reader/books")
    assert full_listing.status_code == 200
    all_books = full_listing.json()
    assert any(book["title"] == GOLDILOCKS_TEST_TITLE and book["is_classic"] for book in all_books)
    assert any(book["title"] != GOLDILOCKS_TEST_TITLE and not book["is_classic"] for book in all_books)

    classic_listing = client.get("/reader/books", params={"is_classic": "true"})
    assert all(book["is_classic"] is True for book in classic_listing.json())

    non_classic_listing = client.get("/reader/books", params={"is_classic": "false"})
    assert all(book["is_classic"] is False for book in non_classic_listing.json())
