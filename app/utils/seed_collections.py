from sqlmodel import Session, select

from app.models import BookCollection


CANONICAL_COLLECTIONS: list[dict[str, str | bool | None]] = [
    {
        "key": "calming_bedtime_stories",
        "title": "Tonight’s Calming Stories",
        "description": "Gentle bedtime picks for winding down together.",
        "language": "en",
        "age_band": "3-7",
        "content_lane_key": "bedtime_3_7",
        "is_public": True,
        "is_featured": True,
    },
    {
        "key": "dolly_daphne_favorites",
        "title": "Dolly & Daphne Favorites",
        "description": "Stories featuring Dolly and Daphne for family read-aloud time.",
        "language": "en",
        "age_band": "3-7",
        "content_lane_key": None,
        "is_public": True,
        "is_featured": True,
    },
    {
        "key": "storylight_guardians",
        "title": "Storylight Guardians",
        "description": "Adventure-forward stories from the Storylight world.",
        "language": "en",
        "age_band": "3-7",
        "content_lane_key": "story_adventures_8_12",
        "is_public": True,
        "is_featured": True,
    },
    {
        "key": "adventures_8_12",
        "title": "Story Adventures",
        "description": "Adventure stories for ages 3-7. (8-12 route to be phased in later.)",
        "language": "en",
        "age_band": "3-7",
        "content_lane_key": "story_adventures_8_12",
        "is_public": True,
        "is_featured": True,
    },
    {
        "key": "spanish_bedtime_stories",
        "title": "Spanish Bedtime Stories",
        "description": "Calming bedtime reads for Spanish-language story time.",
        "language": "es",
        "age_band": "3-7",
        "content_lane_key": "bedtime_3_7",
        "is_public": True,
        "is_featured": False,
    },
]


def seed_collections(session: Session) -> None:
    """Insert canonical discovery collections without duplicating by key. Updates existing to sync age_band."""
    for payload in CANONICAL_COLLECTIONS:
        existing = session.exec(select(BookCollection).where(BookCollection.key == payload["key"])).first()
        if existing is None:
            session.add(BookCollection(**payload))
        else:
            existing.age_band = payload["age_band"]
            existing.title = payload["title"]
            existing.description = payload["description"]
            existing.content_lane_key = payload["content_lane_key"]
            session.add(existing)
    session.commit()
