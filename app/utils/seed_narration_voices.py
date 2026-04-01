from sqlmodel import Session, select

from app.models import NarrationVoice

VOICE_SEED_DATA = [
    {
        "key": "gentle_mother_en",
        "display_name": "Gentle Mother",
        "language": "en",
        "gender": "female",
        "style": "gentle",
        "description": "Warm and reassuring bedtime narration.",
        "is_premium": False,
        "is_active": True,
        "gender_style": "feminine",
        "tone_style": "gentle, nurturing, calm",
    },
    {
        "key": "calm_storyteller_en",
        "display_name": "Calm Storyteller",
        "language": "en",
        "gender": "neutral",
        "style": "calm",
        "description": "Balanced storybook narration for family listening.",
        "is_premium": False,
        "is_active": True,
        "tone_style": "calm, warm, clear",
    },
    {
        "key": "friendly_child_en",
        "display_name": "Friendly Child",
        "language": "en",
        "gender": "neutral",
        "style": "playful",
        "description": "A bright premium child-style narration voice.",
        "is_premium": True,
        "is_active": True,
        "age_style": "child",
        "tone_style": "friendly, curious, playful",
    },
    {
        "key": "calm_storyteller_es",
        "display_name": "Calm Storyteller ES",
        "language": "es",
        "gender": "neutral",
        "style": "calm",
        "description": "Warm Spanish narration for calm listening.",
        "is_premium": False,
        "is_active": True,
        "tone_style": "calm, warm, clear",
    },
    {
        "key": "gentle_mother_fr",
        "display_name": "Gentle Mother FR",
        "language": "fr",
        "gender": "female",
        "style": "gentle",
        "description": "Warm French bedtime narration.",
        "is_premium": False,
        "is_active": True,
        "gender_style": "feminine",
        "tone_style": "gentle, nurturing, calm",
    },
    {
        "key": "calm_storyteller_fr",
        "display_name": "Calm Storyteller FR",
        "language": "fr",
        "gender": "neutral",
        "style": "calm",
        "description": "Balanced French storybook narration for calm family listening.",
        "is_premium": False,
        "is_active": True,
        "tone_style": "calm, warm, clear",
    },
]


def seed_narration_voices(session: Session) -> None:
    """Insert canonical narration voices without duplicating by key."""
    for payload in VOICE_SEED_DATA:
        existing = session.exec(select(NarrationVoice).where(NarrationVoice.key == payload["key"])).first()
        if existing is None:
            session.add(NarrationVoice(**payload))
    session.commit()
