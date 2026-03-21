from app.utils.seed_narration_voices import seed_narration_voices


def seed_voices(session) -> None:
    """Backward-compatible alias for narration voice seeding."""
    seed_narration_voices(session)
