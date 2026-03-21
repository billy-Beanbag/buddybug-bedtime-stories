from sqlmodel import Session, select

from app.models import BetaCohort

DEFAULT_BETA_COHORTS = [
    {
        "key": "narrated_stories_beta",
        "name": "Narrated stories beta",
        "description": "Selected families and staff preview narrated story improvements before full rollout.",
        "is_active": True,
        "feature_flag_keys": "narrated_stories_enabled",
    },
    {
        "key": "offline_sync_beta",
        "name": "Offline sync beta",
        "description": "Controlled preview cohort for offline and sync-related experiences.",
        "is_active": True,
        "feature_flag_keys": "offline_downloads_enabled",
    },
    {
        "key": "creator_tools_beta",
        "name": "Creator tools beta",
        "description": "Internal and partner preview cohort for creator and publishing tooling.",
        "is_active": True,
        "feature_flag_keys": None,
    },
    {
        "key": "educator_beta",
        "name": "Educator beta",
        "description": "Educators and school-friendly partners preview classroom-facing improvements.",
        "is_active": True,
        "feature_flag_keys": None,
    },
    {
        "key": "adventures_8_12_beta",
        "name": "8-12 adventures beta",
        "description": "Selected users preview the 8-12 discovery and reading experience before broad exposure.",
        "is_active": True,
        "feature_flag_keys": "age_band_8_12_enabled",
    },
    {
        "key": "multilingual_beta",
        "name": "Multilingual beta",
        "description": "Controlled multilingual preview cohort for translation and locale-specific UX changes.",
        "is_active": True,
        "feature_flag_keys": None,
    },
]


def seed_beta_cohorts(session: Session) -> None:
    existing_keys = {key for key in session.exec(select(BetaCohort.key)).all()}
    created_any = False
    for payload in DEFAULT_BETA_COHORTS:
        if payload["key"] in existing_keys:
            continue
        session.add(BetaCohort(**payload))
        created_any = True
    if created_any:
        session.commit()
