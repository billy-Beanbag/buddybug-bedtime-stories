from sqlmodel import select

from app.models import BookNarration, NarrationSegment
from app.services.storage_service import build_child_name_audio_path, build_narration_segment_path


def test_voice_list_endpoint_returns_seeded_voices(client):
    response = client.get("/narration/voices?language=en")

    assert response.status_code == 200
    voices = response.json()["voices"]
    voice_keys = {voice["key"] for voice in voices}
    assert "gentle_mother_en" in voice_keys
    assert "calm_storyteller_en" in voice_keys


def test_admin_can_generate_narration_and_segments(client, session, admin_token_headers, demo_published_book):
    response = client.post(
        f"/admin/narration/books/{demo_published_book.id}/generate",
        headers=admin_token_headers,
        json={
            "book_id": demo_published_book.id,
            "voice_key": "gentle_mother_en",
            "language": "en",
            "replace_existing": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["narration"]["book_id"] == demo_published_book.id
    assert payload["segments"]
    assert all("/mock-assets/narration/" in segment["audio_url"] for segment in payload["segments"])

    narration = session.get(BookNarration, payload["narration"]["id"])
    assert narration is not None
    segments = list(session.exec(select(NarrationSegment).where(NarrationSegment.narration_id == narration.id)).all())
    assert len(segments) == len(payload["segments"])


def test_narration_storage_paths_are_provider_aware():
    generated_path = build_narration_segment_path(
        book_id=3,
        voice_key="gentle_mother_en",
        language="en",
        narration_id=5,
        page_number=1,
        provider="elevenlabs",
        extension="mp3",
    )
    mock_path = build_narration_segment_path(
        book_id=3,
        voice_key="gentle_mother_en",
        language="en",
        narration_id=5,
        page_number=1,
        provider="mock",
        extension="wav",
    )
    name_path = build_child_name_audio_path(
        child_profile_id=1,
        voice_key="gentle_mother_en",
        language="en",
        snippet_type="name-only-daphne",
        cache_key="abc123",
        provider="elevenlabs",
        extension="mp3",
    )

    assert generated_path.startswith("generated-assets/narration/")
    assert mock_path.startswith("mock-assets/narration/")
    assert name_path.startswith("generated-assets/narration/names/")


def test_reader_can_fetch_generated_narration(client, admin_token_headers, demo_published_book):
    client.post(
        f"/admin/narration/books/{demo_published_book.id}/generate",
        headers=admin_token_headers,
        json={
            "book_id": demo_published_book.id,
            "voice_key": "calm_storyteller_en",
            "language": "en",
            "replace_existing": True,
        },
    )

    response = client.get(f"/narration/books/{demo_published_book.id}?language=en")

    assert response.status_code == 200
    payload = response.json()
    assert payload["voice"]["key"] == "calm_storyteller_en"
    assert payload["segments"]


def test_workflow_narration_job_succeeds(client, admin_token_headers, demo_published_book):
    response = client.post(
        "/workflows/generate-narration",
        headers=admin_token_headers,
        json={
            "book_id": demo_published_book.id,
            "voice_key": "gentle_mother_en",
            "language": "en",
            "replace_existing": True,
        },
    )

    assert response.status_code == 200
    job = response.json()["job"]
    assert job["job_type"] == "generate_book_narration"

    job_detail = client.get(f"/workflows/jobs/{job['id']}", headers=admin_token_headers)
    assert job_detail.status_code == 200
    assert job_detail.json()["status"] == "succeeded"


def test_premium_voice_requires_premium_access(client, admin_token_headers, user_token_headers, demo_published_book):
    generate_response = client.post(
        f"/admin/narration/books/{demo_published_book.id}/generate",
        headers=admin_token_headers,
        json={
            "book_id": demo_published_book.id,
            "voice_key": "friendly_child_en",
            "language": "en",
            "replace_existing": True,
        },
    )
    assert generate_response.status_code == 201

    response = client.get(
        f"/narration/books/{demo_published_book.id}?language=en&voice_key=friendly_child_en",
        headers=user_token_headers,
    )

    assert response.status_code == 403
