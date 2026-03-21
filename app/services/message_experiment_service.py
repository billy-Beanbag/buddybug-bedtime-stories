from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlmodel import Session

from app.models import User
from app.services.analytics_service import assign_experiment_variant

CopyBundle = dict[str, Any]

MESSAGE_EXPERIMENTS: dict[str, dict[str, Any]] = {
    "homepage_cta_copy": {
        "default_variant": "control",
        "variants": ["control", "routine", "discovery"],
        "copy": {
            "control": {
                "eyebrow": "Buddybug Storylight",
                "headline": "Beautiful bedtime stories for children, powered by imagination.",
                "description": "Illustrated, narrated, calming stories that grow with your family, from cozy bedtime reading to personalized daily story picks.",
                "primary_cta_label": "Start Free",
                "secondary_cta_label": "Explore Stories",
                "pricing_cta_label": "View Pricing",
            },
            "routine": {
                "eyebrow": "Build a calmer routine",
                "headline": "Make bedtime reading easier to repeat night after night.",
                "description": "Buddybug helps families build a gentle routine with illustrated stories, narration, and picks that fit calmer evenings.",
                "primary_cta_label": "Start your bedtime routine",
                "secondary_cta_label": "See tonight's stories",
                "pricing_cta_label": "Compare plans",
            },
            "discovery": {
                "eyebrow": "Story picks that click faster",
                "headline": "Find a great story for tonight without the usual browsing friction.",
                "description": "Open Buddybug to explore bedtime-safe discovery, child-aware picks, and a simple path from free preview to premium access.",
                "primary_cta_label": "Try Buddybug free",
                "secondary_cta_label": "Browse story picks",
                "pricing_cta_label": "See Premium",
            },
        },
    },
    "preview_wall_copy": {
        "default_variant": "control",
        "variants": ["control", "benefits", "gentle_urgency"],
        "copy": {
            "control": {
                "title": "You’ve reached the free preview",
                "description": "Upgrade to keep reading full stories, unlock narrated playback, and save favorites for later.",
                "primary_cta_label": "Upgrade to Premium",
                "guest_primary_label": "Login to upgrade",
                "guest_secondary_label": "Create account",
            },
            "benefits": {
                "title": "Keep the story going with Premium",
                "description": "Premium unlocks full stories, narration, offline-ready saves, and calmer family reading sessions without preview stops.",
                "primary_cta_label": "Unlock full story access",
                "guest_primary_label": "Login for full access",
                "guest_secondary_label": "Create account",
            },
            "gentle_urgency": {
                "title": "Finish tonight’s story without interruption",
                "description": "Premium keeps story time flowing with full reads, audio, and easier saves whenever Buddybug becomes part of your routine.",
                "primary_cta_label": "Continue with Premium",
                "guest_primary_label": "Login to continue",
                "guest_secondary_label": "Start free account",
            },
        },
    },
    "pricing_page_emphasis": {
        "default_variant": "control",
        "variants": ["control", "value", "family"],
        "copy": {
            "control": {
                "headline": "Simple plans for trying Buddybug and upgrading when it clicks",
                "description": "Start with free previews and discovery. Upgrade for full story access, narrated playback, offline-ready saves, premium voices, and richer family personalization.",
                "cta_headline": "Start free today and upgrade when Buddybug becomes part of your routine",
                "cta_description": "Free is enough to explore. Premium is there when your family wants the full bedtime story experience.",
                "primary_cta_label": "Start Free",
                "secondary_cta_label": "Upgrade to Premium",
            },
            "value": {
                "headline": "See the value fast, then upgrade when Buddybug earns a place in your routine",
                "description": "Use free previews to test the experience, then upgrade when your family wants full reads, narration, and easier repeat story nights.",
                "cta_headline": "Start free and unlock more once the value is clear",
                "cta_description": "Premium is built for families ready for fuller story sessions, narration, offline access, and richer personalization.",
                "primary_cta_label": "Start free preview",
                "secondary_cta_label": "See Premium value",
            },
            "family": {
                "headline": "Pricing built for family story time, not for pressure",
                "description": "Try Buddybug at your own pace, then move to Premium when your family wants easier bedtime routines and richer reading tools.",
                "cta_headline": "Start with a calm free experience and upgrade when your family is ready",
                "cta_description": "Premium adds the tools families use most when Buddybug becomes part of regular story time.",
                "primary_cta_label": "Create free account",
                "secondary_cta_label": "Unlock family Premium",
            },
        },
    },
    "premium_upgrade_card_copy": {
        "default_variant": "control",
        "variants": ["control", "benefit_stack", "routine_builder"],
        "copy": {
            "control": {
                "title": "Upgrade when Buddybug becomes part of your routine",
                "description": "Premium unlocks full stories, narration, offline reading, and richer daily recommendations for your family.",
                "cta_label": "Upgrade to Premium",
            },
            "benefit_stack": {
                "title": "Unlock the tools families use most",
                "description": "Premium adds full reads, narrated playback, saved favorites, offline access, and more personal daily picks in one simple step.",
                "cta_label": "See Premium benefits",
            },
            "routine_builder": {
                "title": "Make Buddybug easier to come back to",
                "description": "Premium is designed for families who want bedtime reading to feel smoother, more consistent, and less interrupted.",
                "cta_label": "Start Premium",
            },
        },
    },
}


def _default_bundle(experiment_key: str) -> CopyBundle:
    definition = MESSAGE_EXPERIMENTS[experiment_key]
    variant = definition["default_variant"]
    payload = deepcopy(definition["copy"][variant])
    payload["experiment_key"] = experiment_key
    payload["variant"] = variant
    return payload


def _resolve_variant_bundle(
    session: Session,
    *,
    experiment_key: str,
    user: User | None,
    reader_identifier: str | None,
) -> CopyBundle:
    definition = MESSAGE_EXPERIMENTS[experiment_key]
    if user is None and not (reader_identifier and reader_identifier.strip()):
        return _default_bundle(experiment_key)
    assignment = assign_experiment_variant(
        session,
        experiment_key=experiment_key,
        variants=list(definition["variants"]),
        user=user,
        reader_identifier=reader_identifier,
        sticky=True,
    )
    payload = deepcopy(definition["copy"].get(assignment.variant, definition["copy"][definition["default_variant"]]))
    payload["experiment_key"] = experiment_key
    payload["variant"] = assignment.variant
    return payload


def get_homepage_cta_variant(session: Session, *, user: User | None, reader_identifier: str | None) -> CopyBundle:
    return _resolve_variant_bundle(
        session,
        experiment_key="homepage_cta_copy",
        user=user,
        reader_identifier=reader_identifier,
    )


def get_preview_wall_variant(session: Session, *, user: User | None, reader_identifier: str | None) -> CopyBundle:
    return _resolve_variant_bundle(
        session,
        experiment_key="preview_wall_copy",
        user=user,
        reader_identifier=reader_identifier,
    )


def get_pricing_variant(session: Session, *, user: User | None, reader_identifier: str | None) -> CopyBundle:
    return _resolve_variant_bundle(
        session,
        experiment_key="pricing_page_emphasis",
        user=user,
        reader_identifier=reader_identifier,
    )


def get_upgrade_card_variant(session: Session, *, user: User | None, reader_identifier: str | None) -> CopyBundle:
    return _resolve_variant_bundle(
        session,
        experiment_key="premium_upgrade_card_copy",
        user=user,
        reader_identifier=reader_identifier,
    )


def get_message_experiment_bundle(
    session: Session,
    *,
    user: User | None,
    reader_identifier: str | None,
) -> dict[str, CopyBundle]:
    return {
        "homepage_cta": get_homepage_cta_variant(session, user=user, reader_identifier=reader_identifier),
        "preview_wall": get_preview_wall_variant(session, user=user, reader_identifier=reader_identifier),
        "pricing_page": get_pricing_variant(session, user=user, reader_identifier=reader_identifier),
        "upgrade_card": get_upgrade_card_variant(session, user=user, reader_identifier=reader_identifier),
    }
