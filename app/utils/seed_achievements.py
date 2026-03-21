from sqlmodel import Session

from app.services.achievement_service import seed_achievement_definitions


def seed_achievements(session: Session) -> None:
    """Ensure starter achievement definitions exist."""

    seed_achievement_definitions(session)
