from sqlmodel import Session, select

from app.models import ContentLane

BEDTIME_3_7_LANE_KEY = "bedtime_3_7"
STORY_ADVENTURES_3_7_LANE_KEY = "story_adventures_3_7"
LEGACY_STORY_ADVENTURES_8_12_LANE_KEY = "story_adventures_8_12"
# Compatibility alias while the rest of the codebase finishes moving to the new 3-7 name.
STORY_ADVENTURES_8_12_LANE_KEY = STORY_ADVENTURES_3_7_LANE_KEY

CANONICAL_CONTENT_LANES: list[dict[str, str | bool | None]] = [
    {
        "key": BEDTIME_3_7_LANE_KEY,
        "display_name": "Bedtime Stories 3-7",
        "age_band": "3-7",
        "description": "Calm illustrated bedtime stories for younger children.",
        "tone_rules": "calm, gentle, plot-led, bedtime-safe, warm, never scary",
        "writing_rules": (
            "short read-aloud story format, hook in the opening, small problem introduced early, "
            "clear beginning-middle-end, soothing pacing, simple language, clear sleepy ending, "
            "reduce repetitive poetic moonlight filler"
        ),
        "illustration_rules": "soft watercolor/cartoon bedtime storybook style, warm moonlit lighting, rounded friendly shapes",
        "quality_rules": "strict bedtime safety, gentle ending required, avoid scary conflict",
        "is_active": True,
    },
    {
        "key": STORY_ADVENTURES_3_7_LANE_KEY,
        "display_name": "Story Adventures 3-7",
        "age_band": "3-7",
        "description": "Imaginative story adventures for younger children.",
        "tone_rules": "warm, adventurous, plot-led, emotionally safe, never graphic or disturbing",
        "writing_rules": "richer structure, stronger plot progression, clear hook, central problem or mystery, satisfying ending",
        "illustration_rules": "flexible storybook illustration style, can be more dynamic than bedtime lane while remaining child-friendly",
        "quality_rules": "age-appropriate adventure, no graphic violence, no horror, maintain positive emotional resolution",
        "is_active": True,
    },
]


def seed_content_lanes(session: Session) -> None:
    """Insert canonical content lanes once without duplicating by key. Updates existing lanes to match canonical age_band."""
    for payload in CANONICAL_CONTENT_LANES:
        existing = session.exec(select(ContentLane).where(ContentLane.key == payload["key"])).first()
        if existing is None and payload["key"] == STORY_ADVENTURES_3_7_LANE_KEY:
            existing = session.exec(
                select(ContentLane).where(ContentLane.key == LEGACY_STORY_ADVENTURES_8_12_LANE_KEY)
            ).first()
        if existing is None:
            session.add(ContentLane(**payload))
        else:
            # Keep existing lanes in sync with the canonical route key and age band.
            existing.key = payload["key"]
            existing.age_band = payload["age_band"]
            existing.display_name = payload["display_name"]
            existing.description = payload["description"]
            session.add(existing)
    session.commit()
