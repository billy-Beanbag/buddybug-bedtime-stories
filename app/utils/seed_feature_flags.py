from sqlmodel import Session, select

from app.models import FeatureFlag

DEFAULT_FEATURE_FLAGS = [
    {
        "key": "narrated_stories_enabled",
        "name": "Narrated stories",
        "description": "Controls narrated story playback in reader surfaces.",
        "enabled": True,
        "environments": "development,staging,production",
    },
    {
        "key": "offline_downloads_enabled",
        "name": "Offline downloads",
        "description": "Controls offline save and package download affordances.",
        "enabled": True,
        "environments": "development,staging,production",
        "target_subscription_tiers": "premium",
    },
    {
        "key": "age_band_8_12_enabled",
        "name": "Age band 8-12",
        "description": "Controls gradual exposure of 8-12 discovery surfaces.",
        "enabled": True,
        "environments": "development,staging",
        "target_roles": "admin,editor,premium",
    },
    {
        "key": "editorial_tools_enabled",
        "name": "Editorial tools",
        "description": "Controls internal editorial workflow navigation.",
        "enabled": True,
        "target_roles": "admin,editor",
        "is_internal_only": True,
    },
    {
        "key": "notifications_center_enabled",
        "name": "Notifications center",
        "description": "Controls notification center UI exposure.",
        "enabled": True,
    },
]


def seed_feature_flags(session: Session) -> None:
    """Create starter feature flags without overwriting existing admin choices."""

    existing_keys = {
        key
        for key in session.exec(select(FeatureFlag.key)).all()
    }
    created_any = False
    for payload in DEFAULT_FEATURE_FLAGS:
        if payload["key"] in existing_keys:
            continue
        session.add(FeatureFlag(**payload))
        created_any = True
    if created_any:
        session.commit()
