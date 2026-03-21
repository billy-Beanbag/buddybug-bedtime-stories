from app.services.story_idea_generator import generate_story_idea_payloads as generate_structured_story_idea_payloads


CANONICAL_CHARACTER_ORDER = [
    "Verity",
    "Dolly",
    "Daphne",
    "Buddybug",
    "Glowmoth",
    "Twinklet",
    "Whisperwing",
]


def generate_story_idea_payloads(
    *,
    count: int,
    age_band: str,
    content_lane_key: str | None,
    tone: str,
    include_characters: list[str] | None,
    bedtime_only: bool,
    available_characters: list[str],
) -> list[dict[str, str | int | None]]:
    """Generate hook-first structured story ideas via the Buddybug pipeline."""
    return generate_structured_story_idea_payloads(
        count=count,
        age_band=age_band,
        content_lane_key=content_lane_key,
        tone=tone,
        include_characters=include_characters,
        bedtime_only=bedtime_only,
        available_characters=available_characters,
    )
