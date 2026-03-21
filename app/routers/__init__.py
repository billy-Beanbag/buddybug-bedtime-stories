from app.routers.admin import router as admin_router
from app.routers.analytics import admin_router as analytics_admin_router, router as analytics_router
from app.routers.audit import router as audit_router
from app.routers.automation import router as automation_router
from app.routers.audio import router as audio_router
from app.routers.beta_cohorts import (
    admin_router as beta_cohorts_admin_router,
    membership_router as beta_cohort_memberships_router,
    router as beta_cohorts_router,
)
from app.routers.billing import router as billing_router
from app.routers.books import router as books_router
from app.routers.characters import router as characters_router
from app.routers.child_profiles import router as child_profiles_router
from app.routers.content_lanes import router as content_lanes_router
from app.routers.discovery import admin_router as discovery_admin_router, router as discovery_router
from app.routers.editorial import router as editorial_router
from app.routers.feature_flags import admin_router as feature_flags_admin_router, router as feature_flags_router
from app.routers.feedback import router as feedback_router
from app.routers.growth import admin_router as growth_admin_router, router as growth_router
from app.routers.housekeeping import router as housekeeping_router
from app.routers.i18n import router as i18n_router
from app.routers.illustrations import router as illustrations_router
from app.routers.internal_search import router as internal_search_router
from app.routers.library import admin_router as library_admin_router, router as library_router
from app.routers.maintenance_jobs import router as maintenance_jobs_router
from app.routers.narration import admin_router as narration_admin_router, router as narration_router
from app.routers.notifications import admin_router as notifications_admin_router, router as notifications_router
from app.routers.onboarding import router as onboarding_router
from app.routers.parental_controls import router as parental_controls_router
from app.routers.privacy import admin_router as privacy_admin_router, router as privacy_router
from app.routers.public_status import admin_router as public_status_admin_router, router as public_status_router
from app.routers.quality import admin_router as quality_admin_router, router as quality_router
from app.routers.reader import router as reader_router
from app.routers.reporting import router as reporting_router
from app.routers.recommendations import router as recommendations_router
from app.routers.reviews import router as reviews_router
from app.routers.story_drafts import router as story_drafts_router
from app.routers.story_ideas import router as story_ideas_router
from app.routers.story_pages import router as story_pages_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.support import admin_router as support_admin_router, router as support_router
from app.routers.users import router as users_router
from app.routers.workflows import admin_router as workflows_admin_router, router as workflows_router

__all__ = [
    "admin_router",
    "analytics_admin_router",
    "analytics_router",
    "audit_router",
    "automation_router",
    "audio_router",
    "beta_cohorts_admin_router",
    "beta_cohort_memberships_router",
    "beta_cohorts_router",
    "billing_router",
    "books_router",
    "characters_router",
    "child_profiles_router",
    "content_lanes_router",
    "discovery_admin_router",
    "discovery_router",
    "editorial_router",
    "feature_flags_admin_router",
    "feature_flags_router",
    "feedback_router",
    "growth_admin_router",
    "growth_router",
    "housekeeping_router",
    "i18n_router",
    "illustrations_router",
    "internal_search_router",
    "library_admin_router",
    "library_router",
    "maintenance_jobs_router",
    "narration_admin_router",
    "narration_router",
    "notifications_admin_router",
    "notifications_router",
    "onboarding_router",
    "parental_controls_router",
    "privacy_admin_router",
    "privacy_router",
    "public_status_admin_router",
    "public_status_router",
    "quality_admin_router",
    "quality_router",
    "reader_router",
    "reporting_router",
    "recommendations_router",
    "story_ideas_router",
    "story_drafts_router",
    "story_pages_router",
    "subscriptions_router",
    "support_admin_router",
    "support_router",
    "users_router",
    "workflows_admin_router",
    "workflows_router",
    "reviews_router",
]
