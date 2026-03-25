import json

from app.models import Book, StoryDraft
from app.services.content_lane_service import resolve_content_lane_key
from app.services.quality_service import run_story_draft_quality_checks
from app.services.story_writer import generate_story_draft_payload
from app.services.review_service import utc_now
from tests.utils import create_story_idea_for_lane


def _create_book_for_lane(session, *, age_band: str, content_lane_key: str, published: bool, title_suffix: str) -> Book:
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
        language="en",
        published=published,
        publication_status="published" if published else "ready",
        audio_available=False,
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def test_seeded_content_lanes_can_be_listed(client):
    response = client.get("/content-lanes")

    assert response.status_code == 200
    payload = response.json()
    lane_keys = {item["key"] for item in payload}
    assert "bedtime_3_7" in lane_keys
    assert "story_adventures_3_7" in lane_keys


def test_resolving_age_band_to_lane_works():
    assert resolve_content_lane_key("3-7", None) == "bedtime_3_7"
    assert resolve_content_lane_key("8-12", None) == "story_adventures_3_7"
    assert resolve_content_lane_key(None, None) == "bedtime_3_7"


def test_3_7_idea_generation_uses_bedtime_lane(client):
    response = client.post(
        "/story-ideas/generate",
        json={"count": 1, "age_band": "3-7", "bedtime_only": True},
    )

    assert response.status_code == 201
    idea = response.json()["ideas"][0]
    assert idea["age_band"] == "3-7"
    assert idea["content_lane_key"] == "bedtime_3_7"


def test_8_12_idea_generation_uses_adventure_lane(client, admin_token_headers):
    response = client.post(
        "/story-ideas/generate",
        json={"count": 1, "age_band": "8-12", "content_lane_key": "story_adventures_3_7", "bedtime_only": False},
        headers=admin_token_headers,
    )

    assert response.status_code == 201
    idea = response.json()["ideas"][0]
    assert idea["age_band"] == "8-12"
    assert idea["content_lane_key"] == "story_adventures_3_7"


def test_8_12_draft_generation_produces_correct_lane_key(client, admin_token_headers, editor_token_headers):
    idea_response = client.post(
        "/story-ideas/generate",
        json={"count": 1, "age_band": "8-12", "content_lane_key": "story_adventures_3_7", "bedtime_only": False},
        headers=admin_token_headers,
    )
    idea_id = idea_response.json()["ideas"][0]["id"]

    draft_response = client.post("/story-drafts/generate", json={"story_idea_id": idea_id}, headers=editor_token_headers)

    assert draft_response.status_code == 201
    draft = draft_response.json()
    assert draft["content_lane_key"] == "story_adventures_3_7"
    assert draft["read_time_minutes"] >= 7


def test_bedtime_drafts_open_with_a_clear_plot_hook(client, admin_token_headers, editor_token_headers):
    idea_response = client.post(
        "/story-ideas/generate",
        json={"count": 1, "age_band": "3-7", "bedtime_only": True},
        headers=admin_token_headers,
    )
    idea_id = idea_response.json()["ideas"][0]["id"]

    draft_response = client.post("/story-drafts/generate", json={"story_idea_id": idea_id}, headers=editor_token_headers)

    assert draft_response.status_code == 201
    first_paragraph = draft_response.json()["full_text"].split("\n\n")[0].lower()
    assert any(token in first_paragraph for token in {"just as", "just before bed", "noticed", "discovered"})
    assert any(token in first_paragraph for token in {"problem", "mystery", "missing", "question", "puzzling"})


def test_non_bedtime_3_7_generation_allows_playful_story_mode(client, admin_token_headers, editor_token_headers):
    idea_response = client.post(
        "/story-ideas/generate",
        json={
            "count": 1,
            "age_band": "3-7",
            "bedtime_only": False,
            "tone": "warm, playful, cheeky, plot-led",
        },
        headers=admin_token_headers,
    )

    assert idea_response.status_code == 201
    idea = idea_response.json()["ideas"][0]
    assert "playful" in idea["tone"].lower()
    premise_l = idea["premise"].lower()
    assert any(
        token in premise_l
        for token in {
            "muddle",
            "fun",
            "surprise",
            "clue",
            "pond",
            "puddle",
            "jump",
            "hole",
            "shortcut",
            "garden",
            "trail",
            "missing",
            "lost",
            "disappear",
        }
    )

    draft_response = client.post("/story-drafts/generate", json={"story_idea_id": idea["id"]}, headers=editor_token_headers)
    assert draft_response.status_code == 201
    full_text = draft_response.json()["full_text"].lower()
    assert any(token in full_text for token in {"playful", "muddle", "fun", "laugh"})
    assert full_text.count("moonlight") == 0


def test_quality_checks_behave_differently_by_lane(session):
    bedtime_idea = create_story_idea_for_lane(session, age_band="3-7", content_lane_key="bedtime_3_7")
    adventure_idea = create_story_idea_for_lane(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
    )
    bedtime_text = ("Verity and Buddybug solved the puzzle together. " * 140).strip()
    adventure_text = ("Verity and Buddybug solved the puzzle together and headed home hopeful. " * 140).strip()

    bedtime_draft = StoryDraft(
        story_idea_id=bedtime_idea.id,
        title="Bedtime lane quality test",
        content_lane_key="bedtime_3_7",
        full_text=bedtime_text,
        summary="Bedtime test",
        read_time_minutes=6,
        review_status="draft_pending_review",
        generation_source="manual",
        updated_at=utc_now(),
    )
    adventure_draft = StoryDraft(
        story_idea_id=adventure_idea.id,
        title="Adventure lane quality test",
        content_lane_key="story_adventures_3_7",
        full_text=adventure_text,
        summary="Adventure test",
        read_time_minutes=8,
        review_status="draft_pending_review",
        generation_source="manual",
        updated_at=utc_now(),
    )
    session.add(bedtime_draft)
    session.add(adventure_draft)
    session.commit()
    session.refresh(bedtime_draft)
    session.refresh(adventure_draft)

    bedtime_checks = run_story_draft_quality_checks(session, story_draft_id=bedtime_draft.id)
    adventure_checks = run_story_draft_quality_checks(session, story_draft_id=adventure_draft.id)

    bedtime_structure = next(check for check in bedtime_checks if check.check_type == "structure_quality")
    adventure_structure = next(check for check in adventure_checks if check.check_type == "structure_quality")
    bedtime_issue_codes = {item["code"] for item in json.loads(bedtime_structure.issues_json or "[]")}
    adventure_issue_codes = {item["code"] for item in json.loads(adventure_structure.issues_json or "[]")}

    assert "calm_ending_missing" in bedtime_issue_codes
    assert "calm_ending_missing" not in adventure_issue_codes


def test_reader_and_recommendation_age_band_filters_exclude_unpublished_books(client, session):
    published_8_12 = _create_book_for_lane(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        published=True,
        title_suffix="Published",
    )
    _create_book_for_lane(
        session,
        age_band="8-12",
        content_lane_key="story_adventures_3_7",
        published=False,
        title_suffix="Unpublished",
    )
    _create_book_for_lane(
        session,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        published=True,
        title_suffix="Young",
    )

    reader_response = client.get("/reader/books?age_band=8-12")
    recommendations_response = client.get("/recommendations/fallback?age_band=8-12")

    assert reader_response.status_code == 200
    reader_books = reader_response.json()
    assert all(book["age_band"] == "8-12" for book in reader_books)
    assert {book["book_id"] for book in reader_books} == {published_8_12.id}

    assert recommendations_response.status_code == 200
    recommended_items = recommendations_response.json()["items"]
    assert recommended_items
    assert all(item["age_band"] == "8-12" for item in recommended_items)
    assert {item["book_id"] for item in recommended_items} == {published_8_12.id}
