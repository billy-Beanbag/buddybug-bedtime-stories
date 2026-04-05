from __future__ import annotations

from sqlmodel import Session

from app.models import ClassicSource, User
from app.services.classics_service import create_classic_source

GOLDILOCKS_TEST_TITLE = "Goldilocks and the Three Bears"
GOLDILOCKS_TEST_SOURCE_URL = "https://example.org/public-domain/goldilocks-test-fixture"
GOLDILOCKS_TEST_SOURCE_AUTHOR = "Traditional / public-domain test fixture"
GOLDILOCKS_TEST_SOURCE_TEXT = (
    "Once upon a time there were three bears who lived together in a little house in the forest.\n\n"
    "One morning they made porridge for breakfast, but it was too hot to eat, so they went out for a walk while it cooled.\n\n"
    "While they were away, a little girl named Goldilocks came to the house. She tasted the porridge, tried the chairs, and then went upstairs.\n\n"
    "There she found the beds, and because the little bed felt just right, she curled up in it and fell asleep.\n\n"
    "When the bears came home, they discovered what had happened. Goldilocks woke up, saw the bears, and hurried away from the house as fast as she could."
)

LITTLE_RED_TEST_TITLE = "Little Red Riding Hood"
LITTLE_RED_TEST_SOURCE_URL = "https://example.org/public-domain/little-red-riding-hood-test-fixture"
LITTLE_RED_TEST_SOURCE_AUTHOR = "Traditional / public-domain test fixture"
LITTLE_RED_TEST_SOURCE_TEXT = (
    "Once upon a time there was a little girl who was known as Little Red Riding Hood because of the red hooded cloak she wore.\n\n"
    "One day her mother asked her to take a basket of food to her grandmother and told her to stay on the woodland path.\n\n"
    "On the way, she met a wolf, who spoke to her and learned where she was going.\n\n"
    "The wolf hurried ahead to grandmother's cottage, while Little Red Riding Hood paused among the flowers and then continued on her way.\n\n"
    "When she arrived, she soon realized something was wrong, and in the end the wolf was defeated and Little Red Riding Hood was safe again."
)


def build_goldilocks_classic_payload() -> dict[str, object]:
    return {
        "title": GOLDILOCKS_TEST_TITLE,
        "source_text": GOLDILOCKS_TEST_SOURCE_TEXT,
        "source_url": GOLDILOCKS_TEST_SOURCE_URL,
        "public_domain_verified": True,
        "source_author": GOLDILOCKS_TEST_SOURCE_AUTHOR,
        "source_origin_notes": "Internal QA fixture for the Buddybug Classics pipeline.",
    }


def build_little_red_classic_payload() -> dict[str, object]:
    return {
        "title": LITTLE_RED_TEST_TITLE,
        "source_text": LITTLE_RED_TEST_SOURCE_TEXT,
        "source_url": LITTLE_RED_TEST_SOURCE_URL,
        "public_domain_verified": True,
        "source_author": LITTLE_RED_TEST_SOURCE_AUTHOR,
        "source_origin_notes": "Second internal QA fixture for the Buddybug Classics pipeline.",
    }


def create_goldilocks_classic_source(session: Session, *, current_user: User) -> ClassicSource:
    payload = build_goldilocks_classic_payload()
    return create_classic_source_from_payload(session, current_user=current_user, payload=payload)


def create_little_red_classic_source(session: Session, *, current_user: User) -> ClassicSource:
    payload = build_little_red_classic_payload()
    return create_classic_source_from_payload(session, current_user=current_user, payload=payload)


def create_classic_source_from_payload(
    session: Session,
    *,
    current_user: User,
    payload: dict[str, object],
) -> ClassicSource:
    return create_classic_source(
        session,
        current_user=current_user,
        title=str(payload["title"]),
        source_text=str(payload["source_text"]),
        source_url=str(payload["source_url"]),
        public_domain_verified=bool(payload["public_domain_verified"]),
        source_author=str(payload["source_author"]),
        source_origin_notes=str(payload["source_origin_notes"]),
    )
