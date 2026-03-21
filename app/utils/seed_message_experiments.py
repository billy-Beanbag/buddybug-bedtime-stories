from sqlmodel import Session

MESSAGE_EXPERIMENT_KEYS = [
    "homepage_cta_copy",
    "preview_wall_copy",
    "pricing_page_emphasis",
    "premium_upgrade_card_copy",
]


def seed_message_experiments(session: Session) -> None:
    """Message experiments use sticky runtime assignments, so the seed is a lightweight registry hook."""
    _ = session
