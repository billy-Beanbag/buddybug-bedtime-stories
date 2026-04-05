import logging
from pathlib import Path
from time import perf_counter
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles
from sqlmodel import Session

from app.config import (
    APP_NAME,
    CORS_ALLOW_ORIGIN_REGEX,
    CORS_ALLOW_ORIGINS,
    DEBUG,
    PROJECT_ROOT,
    STORAGE_LOCAL_BASE_PATH,
)
from app.database import engine, ensure_sqlite_schema_compatibility, get_session, required_tables_exist
from app.errors import http_exception_handler, unhandled_exception_handler
from app.logging_config import configure_logging
from app.middleware.request_context import RequestContextMiddleware, get_request_id_from_request
from app.routers.admin import router as admin_router
from app.routers.system import router as system_router
from app.routers.account_health import router as account_health_router
from app.routers.activity_feed import router as activity_feed_router
from app.routers.achievements import admin_router as achievements_admin_router, router as achievements_router
from app.routers.analytics import admin_router as analytics_admin_router, router as analytics_router
from app.routers.api_keys import admin_router as api_keys_admin_router, router as api_keys_router
from app.routers.audit import router as audit_router
from app.routers.automation import router as automation_router
from app.routers.audio import router as audio_router
from app.routers.beta_cohorts import (
    admin_router as beta_cohorts_admin_router,
    membership_router as beta_cohort_memberships_router,
    router as beta_cohorts_router,
)
from app.routers.bedtime_packs import router as bedtime_packs_router
from app.routers.billing_recovery import admin_router as billing_recovery_admin_router, router as billing_recovery_router
from app.routers.billing import router as billing_router
from app.routers.books import router as books_router
from app.routers.characters import router as characters_router
from app.routers.changelog import admin_router as changelog_admin_router, router as changelog_router
from app.routers.child_comfort import router as child_comfort_router
from app.routers.child_profiles import router as child_profiles_router
from app.routers.classics import router as classics_router
from app.routers.content_lanes import router as content_lanes_router
from app.routers.content_versions import router as content_versions_router
from app.routers.discovery import admin_router as discovery_admin_router, router as discovery_router
from app.routers.educator import router as educator_router
from app.routers.editorial import router as editorial_router
from app.routers.feature_flags import admin_router as feature_flags_admin_router, router as feature_flags_router
from app.routers.family_digest import admin_router as family_digest_admin_router, router as family_digest_router
from app.routers.feedback import router as feedback_router
from app.routers.growth import admin_router as growth_admin_router, router as growth_router
from app.routers.housekeeping import router as housekeeping_router
from app.routers.i18n import router as i18n_router
from app.routers.illustrations import router as illustrations_router
from app.routers.incidents import router as incidents_router
from app.routers.internal_search import router as internal_search_router
from app.routers.library import admin_router as library_admin_router, router as library_router
from app.routers.lifecycle import router as lifecycle_router
from app.routers.maintenance_jobs import router as maintenance_jobs_router
from app.routers.message_experiments import router as message_experiments_router
from app.routers.moderation import router as moderation_router
from app.routers.narration import admin_router as narration_admin_router, router as narration_router
from app.routers.notifications import admin_router as notifications_admin_router, router as notifications_router
from app.routers.onboarding import router as onboarding_router
from app.routers.organizations import router as organizations_router
from app.routers.parental_controls import router as parental_controls_router
from app.routers.privacy import admin_router as privacy_admin_router, router as privacy_router
from app.routers.public_status import admin_router as public_status_admin_router, router as public_status_router
from app.routers.promo_access import admin_router as promo_access_admin_router, router as promo_access_router
from app.routers.quality import admin_router as quality_admin_router, router as quality_router
from app.routers.read_along import router as read_along_router
from app.routers.reading_plans import router as reading_plans_router
from app.routers.reader import router as reader_router
from app.routers.reengagement import admin_router as reengagement_admin_router, router as reengagement_router
from app.routers.reporting import router as reporting_router
from app.routers.recommendations import router as recommendations_router
from app.routers.reviews import router as reviews_router
from app.routers.seasonal_campaigns import (
    admin_item_router as seasonal_campaign_items_admin_router,
    admin_router as seasonal_campaigns_admin_router,
    router as seasonal_campaigns_router,
)
from app.routers.story_drafts import router as story_drafts_router
from app.routers.story_ideas import router as story_ideas_router
from app.routers.story_pages import router as story_pages_router
from app.routers.story_suggestions import admin_router as story_suggestions_admin_router, router as story_suggestions_router
from app.routers.story_quality import admin_router as story_quality_admin_router, router as story_quality_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.support import admin_router as support_admin_router, router as support_router
from app.routers.translation_ops import router as translation_ops_router
from app.routers.users import router as users_router
from app.routers.visual_references import router as visual_references_router
from app.routers.workflows import admin_router as workflows_admin_router, router as workflows_router
from app.utils.seed_characters import seed_characters
from app.utils.seed_beta_cohorts import seed_beta_cohorts
from app.utils.seed_collections import seed_collections
from app.utils.seed_content_lanes import seed_content_lanes
from app.utils.seed_achievements import seed_achievements
from app.utils.seed_feature_flags import seed_feature_flags
from app.utils.seed_housekeeping_policies import seed_housekeeping_policies
from app.utils.seed_message_experiments import seed_message_experiments
from app.utils.seed_public_status_components import seed_public_status_components
from app.utils.seed_seasonal_campaigns import seed_seasonal_campaigns
from app.utils.seed_voices import seed_voices

configure_logging()
logger = logging.getLogger(__name__)
request_logger = logging.getLogger("buddybug.request")


@asynccontextmanager
async def lifespan(_: FastAPI):
    applied_schema_changes = ensure_sqlite_schema_compatibility()
    if applied_schema_changes:
        logger.info("Applied local SQLite schema compatibility fixes: %s", ", ".join(applied_schema_changes))
    if required_tables_exist("character", "narrationvoice", "contentlane", "bookcollection"):
        with Session(engine) as session:
            seed_characters(session)
            seed_content_lanes(session)
            seed_voices(session)
            seed_collections(session)
            if required_tables_exist("featureflag"):
                seed_feature_flags(session)
            if required_tables_exist("betacohort", "betacohortmembership"):
                seed_beta_cohorts(session)
            if required_tables_exist("housekeepingpolicy", "housekeepingrun"):
                seed_housekeeping_policies(session)
            if required_tables_exist("publicstatuscomponent", "publicstatusnotice"):
                seed_public_status_components(session)
            if required_tables_exist("achievementdefinition"):
                seed_achievements(session)
            seed_message_experiments(session)
            if required_tables_exist("seasonalcampaign", "seasonalcampaignitem", "book"):
                seed_seasonal_campaigns(session)
            if required_tables_exist("user"):
                from app.utils.dev_seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, ensure_demo_user

                ensure_demo_user(
                    session,
                    email=DEMO_ADMIN_EMAIL,
                    password=DEMO_ADMIN_PASSWORD,
                    display_name="Buddybug Admin",
                    is_admin=True,
                    subscription_tier="premium",
                    subscription_status="active",
                )
                logger.info("Ensured demo admin user %s", DEMO_ADMIN_EMAIL)
    else:
        logger.info("Skipping startup reference seeding because database migrations have not been applied yet.")
    yield


app = FastAPI(title=APP_NAME, debug=DEBUG, lifespan=lifespan)
logger.info(
    "CORS allow_origins count=%s regex=%s",
    len(CORS_ALLOW_ORIGINS),
    repr(CORS_ALLOW_ORIGIN_REGEX) if CORS_ALLOW_ORIGIN_REGEX else None,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_origin_regex=CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
mock_assets_dir = Path(STORAGE_LOCAL_BASE_PATH) / "mock-assets"
mock_assets_dir.mkdir(parents=True, exist_ok=True)
app.mount("/mock-assets", StaticFiles(directory=mock_assets_dir), name="mock-assets")
generated_assets_dir = Path(STORAGE_LOCAL_BASE_PATH) / "generated-assets"
generated_assets_dir.mkdir(parents=True, exist_ok=True)
app.mount("/generated-assets", StaticFiles(directory=generated_assets_dir), name="generated-assets")
artwork_dir = PROJECT_ROOT / "Artwork"
if artwork_dir.exists():
    app.mount("/artwork-assets", StaticFiles(directory=artwork_dir), name="artwork-assets")
app.include_router(system_router)  # First: health, login-check, ready
app.include_router(admin_router)
app.include_router(account_health_router)
app.include_router(activity_feed_router)
app.include_router(achievements_router)
app.include_router(achievements_admin_router)
app.include_router(analytics_router)
app.include_router(analytics_admin_router)
app.include_router(api_keys_router)
app.include_router(api_keys_admin_router)
app.include_router(audit_router)
app.include_router(automation_router)
app.include_router(audio_router)
app.include_router(beta_cohorts_router)
app.include_router(beta_cohorts_admin_router)
app.include_router(beta_cohort_memberships_router)
app.include_router(bedtime_packs_router)
app.include_router(billing_recovery_router)
app.include_router(billing_recovery_admin_router)
app.include_router(billing_router)
app.include_router(books_router)
app.include_router(characters_router)
app.include_router(changelog_router)
app.include_router(changelog_admin_router)
app.include_router(child_comfort_router)
app.include_router(child_profiles_router)
app.include_router(classics_router)
app.include_router(content_lanes_router)
app.include_router(content_versions_router)
app.include_router(discovery_router)
app.include_router(discovery_admin_router)
app.include_router(educator_router)
app.include_router(editorial_router)
app.include_router(feature_flags_router)
app.include_router(feature_flags_admin_router)
app.include_router(family_digest_router)
app.include_router(family_digest_admin_router)
app.include_router(feedback_router)
app.include_router(growth_router)
app.include_router(growth_admin_router)
app.include_router(housekeeping_router)
app.include_router(i18n_router)
app.include_router(incidents_router)
app.include_router(internal_search_router)
app.include_router(quality_router)
app.include_router(quality_admin_router)
app.include_router(read_along_router)
app.include_router(reading_plans_router)
app.include_router(library_router)
app.include_router(library_admin_router)
app.include_router(lifecycle_router)
app.include_router(maintenance_jobs_router)
app.include_router(message_experiments_router)
app.include_router(moderation_router)
app.include_router(narration_router)
app.include_router(narration_admin_router)
app.include_router(notifications_router)
app.include_router(notifications_admin_router)
app.include_router(onboarding_router)
app.include_router(organizations_router)
app.include_router(parental_controls_router)
app.include_router(privacy_router)
app.include_router(privacy_admin_router)
app.include_router(public_status_router)
app.include_router(public_status_admin_router)
app.include_router(promo_access_router)
app.include_router(promo_access_admin_router)
app.include_router(reengagement_router)
app.include_router(reengagement_admin_router)
app.include_router(seasonal_campaigns_router)
app.include_router(seasonal_campaigns_admin_router)
app.include_router(seasonal_campaign_items_admin_router)
app.include_router(story_ideas_router)
app.include_router(story_drafts_router)
app.include_router(reviews_router)
app.include_router(story_pages_router)
app.include_router(story_suggestions_router)
app.include_router(story_suggestions_admin_router)
app.include_router(story_quality_router)
app.include_router(story_quality_admin_router)
app.include_router(illustrations_router)
app.include_router(reader_router)
app.include_router(reporting_router)
app.include_router(recommendations_router)
app.include_router(subscriptions_router)
app.include_router(support_router)
app.include_router(support_admin_router)
app.include_router(translation_ops_router)
app.include_router(users_router)
app.include_router(visual_references_router)
app.include_router(workflows_router)
app.include_router(workflows_admin_router)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        request_logger.exception(
            "request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "request_id": get_request_id_from_request(request),
            },
        )
        raise
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    request_logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "request_id": get_request_id_from_request(request),
        },
    )
    return response


@app.get("/health", tags=["system"])
def health(
    login_check: bool = Query(default=False, alias="login_check"),
    session: Session = Depends(get_session),
):
    """Health. Add ?login_check=1 to diagnose admin login."""
    out: dict = {"status": "ok", "app": APP_NAME}
    if login_check and str(login_check).lower() in ("1", "true", "yes"):
        from sqlmodel import select

        from app.models import User
        from app.utils.auth import verify_password
        from app.utils.dev_seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD

        user = session.exec(select(User).where(User.email == DEMO_ADMIN_EMAIL.lower())).first()
        if not user:
            out["admin_exists"] = False
            out["hint"] = "Run: python scripts/fix_dev_setup.py then restart backend"
        else:
            pw_ok = verify_password(DEMO_ADMIN_PASSWORD, user.password_hash)
            out["admin_exists"] = True
            out["password_ok"] = pw_ok
            out["email"] = DEMO_ADMIN_EMAIL
            out["hint"] = "Login should work" if pw_ok else "Password wrong - restart backend to fix"
    return out


@app.post("/dev/seed-admin", tags=["system"])
def dev_seed_admin(session: Session = Depends(get_session)) -> JSONResponse:
    """Create/update demo admin. Run before login if login fails."""
    from app.utils.dev_seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, ensure_demo_user

    user = ensure_demo_user(
        session,
        email=DEMO_ADMIN_EMAIL,
        password=DEMO_ADMIN_PASSWORD,
        display_name="Buddybug Admin",
        is_admin=True,
        subscription_tier="premium",
        subscription_status="active",
    )
    return JSONResponse(
        status_code=200,
        content={"ok": True, "email": user.email, "hint": "Now try logging in with Admin123!"},
    )

