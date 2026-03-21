from sqlmodel import Session, select

from app.models import PublicStatusComponent

DEFAULT_PUBLIC_STATUS_COMPONENTS = [
    {
        "key": "reading",
        "name": "Reading & Library",
        "description": "Reading, saved library access, and story playback surfaces.",
        "sort_order": 10,
        "is_active": True,
        "current_status": "operational",
    },
    {
        "key": "audio",
        "name": "Narrated Stories",
        "description": "Narrated playback and audio delivery for supported stories.",
        "sort_order": 20,
        "is_active": True,
        "current_status": "operational",
    },
    {
        "key": "billing",
        "name": "Billing & Premium",
        "description": "Premium signup, subscription changes, and billing support surfaces.",
        "sort_order": 30,
        "is_active": True,
        "current_status": "operational",
    },
    {
        "key": "login",
        "name": "Login & Accounts",
        "description": "Authentication and account access for families and partners.",
        "sort_order": 40,
        "is_active": True,
        "current_status": "operational",
    },
]


def seed_public_status_components(session: Session) -> None:
    existing_keys = {key for key in session.exec(select(PublicStatusComponent.key)).all()}
    created_any = False
    for payload in DEFAULT_PUBLIC_STATUS_COMPONENTS:
        if payload["key"] in existing_keys:
            continue
        session.add(PublicStatusComponent(**payload))
        created_any = True
    if created_any:
        session.commit()
