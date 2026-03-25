from datetime import timedelta

from app.services.review_service import utc_now
from tests.utils import create_demo_pipeline


def test_active_campaign_filtering_by_date_works(client, editor_token_headers):
    now = utc_now()
    active_payload = {
        "key": "spring_storylight_test",
        "title": "Spring Storylight Test",
        "description": "Active campaign",
        "start_at": (now - timedelta(days=5)).isoformat(),
        "end_at": (now + timedelta(days=30)).isoformat(),
        "is_active": True,
        "language": "en",
        "age_band": "3-7",
        "content_lane_key": "bedtime_3_7",
    }
    expired_payload = {
        "key": "expired_storylight_test",
        "title": "Expired Storylight Test",
        "description": "Expired campaign",
        "start_at": (now - timedelta(days=30)).isoformat(),
        "end_at": (now - timedelta(days=15)).isoformat(),
        "is_active": True,
        "language": "en",
        "age_band": "3-7",
    }

    client.post("/admin/campaigns", headers=editor_token_headers, json=active_payload)
    client.post("/admin/campaigns", headers=editor_token_headers, json=expired_payload)

    response = client.get("/campaigns/active", params={"language": "en", "age_band": "3-7"})

    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    assert "spring_storylight_test" in keys
    assert "expired_storylight_test" not in keys


def test_campaign_detail_returns_ordered_books(client, session, demo_published_book, editor_token_headers):
    now = utc_now()
    second_book = create_demo_pipeline(session, idea_index=1)["book"]
    campaign = client.post(
        "/admin/campaigns",
        headers=editor_token_headers,
        json={
            "key": "cozy_bedtime_detail_test",
            "title": "Cozy Bedtime Detail Test",
            "description": "Ordered books",
            "start_at": (now - timedelta(days=3)).isoformat(),
            "end_at": (now + timedelta(days=20)).isoformat(),
            "is_active": True,
            "language": "en",
            "age_band": "3-7",
            "content_lane_key": "bedtime_3_7",
        },
    ).json()
    client.post(
        f"/admin/campaigns/{campaign['id']}/items",
        headers=editor_token_headers,
        json={"book_id": second_book.id, "position": 1},
    )
    client.post(
        f"/admin/campaigns/{campaign['id']}/items",
        headers=editor_token_headers,
        json={"book_id": demo_published_book.id, "position": 2},
    )

    response = client.get(f"/campaigns/{campaign['key']}")

    assert response.status_code == 200
    item_ids = [item["book_id"] for item in response.json()["items"]]
    assert item_ids == [second_book.id, demo_published_book.id]


def test_campaign_filters_by_language_and_age_band(client, editor_token_headers):
    now = utc_now()
    client.post(
        "/admin/campaigns",
        headers=editor_token_headers,
        json={
            "key": "older_reader_campaign_test",
            "title": "Older Reader Campaign",
            "description": "8-12 only",
            "start_at": (now - timedelta(days=1)).isoformat(),
            "end_at": (now + timedelta(days=25)).isoformat(),
            "is_active": True,
            "language": "en",
            "age_band": "8-12",
            "content_lane_key": "story_adventures_3_7",
        },
    )

    filtered_out = client.get("/campaigns/active", params={"language": "en", "age_band": "3-7"})
    filtered_in = client.get("/campaigns/active", params={"language": "en", "age_band": "8-12"})

    assert filtered_out.status_code == 200
    assert all(item["key"] != "older_reader_campaign_test" for item in filtered_out.json())
    assert any(item["key"] == "older_reader_campaign_test" for item in filtered_in.json())


def test_admin_campaign_crud_works(client, editor_token_headers, demo_published_book):
    now = utc_now()
    create_response = client.post(
        "/admin/campaigns",
        headers=editor_token_headers,
        json={
            "key": "crud_campaign_test",
            "title": "CRUD Campaign Test",
            "description": "Editable campaign",
            "start_at": (now - timedelta(days=2)).isoformat(),
            "end_at": (now + timedelta(days=10)).isoformat(),
            "is_active": True,
            "language": "en",
            "age_band": "3-7",
        },
    )
    assert create_response.status_code == 201
    campaign = create_response.json()

    item_response = client.post(
        f"/admin/campaigns/{campaign['id']}/items",
        headers=editor_token_headers,
        json={"book_id": demo_published_book.id, "position": 1},
    )
    assert item_response.status_code == 201

    list_response = client.get("/admin/campaigns", headers=editor_token_headers)
    assert any(item["id"] == campaign["id"] for item in list_response.json())

    patch_response = client.patch(
        f"/admin/campaigns/{campaign['id']}",
        headers=editor_token_headers,
        json={"title": "Updated Campaign Test", "homepage_badge_text": "Seasonal"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Updated Campaign Test"

    delete_item_response = client.delete(
        f"/admin/campaign-items/{item_response.json()['id']}",
        headers=editor_token_headers,
    )
    assert delete_item_response.status_code == 204

    delete_campaign_response = client.delete(f"/admin/campaigns/{campaign['id']}", headers=editor_token_headers)
    assert delete_campaign_response.status_code == 204
