from __future__ import annotations

import hashlib
from dataclasses import dataclass

from fastapi import Request
from sqlmodel import Session, select

from app.config import APP_ENV
from app.middleware.request_context import get_request_id_from_request
from app.models import ChildProfile, FeatureFlag, User
from app.schemas.feature_flag_schema import FeatureFlagEvaluationResponse
from app.services.beta_cohort_service import get_user_beta_cohort_keys


@dataclass(frozen=True)
class FeatureFlagContext:
    environment: str
    user: User | None
    child_profile: ChildProfile | None
    language: str | None
    country: str | None
    subscription_tier: str | None
    roles: set[str]
    beta_cohort_keys: set[str]
    identity: str

    @property
    def user_id(self) -> int | None:
        return self.user.id if self.user is not None else None

    @property
    def age_band(self) -> str | None:
        return self.child_profile.age_band if self.child_profile is not None else None


def parse_csv_set(value: str | None) -> set[str]:
    if value is None:
        return set()
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def get_feature_flag_by_key(session: Session, key: str) -> FeatureFlag | None:
    statement = select(FeatureFlag).where(FeatureFlag.key == key)
    return session.exec(statement).first()


def list_feature_flags(session: Session) -> list[FeatureFlag]:
    statement = select(FeatureFlag).order_by(FeatureFlag.key.asc())
    return list(session.exec(statement).all())


def bucket_user_for_rollout(*, flag_key: str, identity: str) -> int:
    digest = hashlib.sha256(f"{flag_key}:{identity}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def build_feature_flag_context(
    session: Session,
    *,
    request: Request,
    current_user: User | None,
    child_profile_id: int | None,
    language: str | None,
) -> FeatureFlagContext:
    child_profile = _get_context_child_profile(session, current_user=current_user, child_profile_id=child_profile_id)
    resolved_language = (language or (child_profile.language if child_profile is not None else None) or (
        current_user.language if current_user is not None else None
    ))
    resolved_country = (
        (current_user.country if current_user is not None else None)
        or request.headers.get("X-Country")
        or request.headers.get("CF-IPCountry")
    )
    roles = _build_roles(current_user)
    identity = _resolve_identity(request=request, current_user=current_user)
    subscription_tier = current_user.subscription_tier.lower() if current_user is not None else None
    return FeatureFlagContext(
        environment=APP_ENV.lower(),
        user=current_user,
        child_profile=child_profile,
        language=resolved_language.lower() if resolved_language else None,
        country=resolved_country.lower() if resolved_country else None,
        subscription_tier=subscription_tier,
        roles=roles,
        beta_cohort_keys=get_user_beta_cohort_keys(session, user_id=current_user.id) if current_user is not None else set(),
        identity=identity,
    )


def context_matches_flag(flag: FeatureFlag, context: FeatureFlagContext) -> tuple[bool, str]:
    environments = parse_csv_set(flag.environments)
    if environments and context.environment not in environments:
        return False, "environment mismatch"

    if flag.is_internal_only and not {"admin", "editor"} & context.roles:
        return False, "internal access required"

    target_user_ids = parse_csv_set(flag.target_user_ids)
    if target_user_ids and (context.user_id is None or str(context.user_id) not in target_user_ids):
        return False, "user not explicitly targeted"

    allowed_tiers = parse_csv_set(flag.target_subscription_tiers)
    if allowed_tiers and (context.subscription_tier is None or context.subscription_tier not in allowed_tiers):
        return False, "subscription tier not allowed"

    allowed_languages = parse_csv_set(flag.target_languages)
    if allowed_languages and (context.language is None or context.language not in allowed_languages):
        return False, "language not allowed"

    allowed_age_bands = parse_csv_set(flag.target_age_bands)
    if allowed_age_bands and (context.age_band is None or context.age_band.lower() not in allowed_age_bands):
        return False, "age band not allowed"

    allowed_roles = parse_csv_set(flag.target_roles)
    if allowed_roles and not context.roles.intersection(allowed_roles):
        return False, "role not allowed"

    allowed_countries = parse_csv_set(flag.target_countries)
    if allowed_countries and (context.country is None or context.country not in allowed_countries):
        return False, "country not allowed"

    required_beta_cohorts = parse_csv_set(flag.target_beta_cohorts)
    if required_beta_cohorts and not context.beta_cohort_keys.intersection(required_beta_cohorts):
        return False, "beta cohort not allowed"

    if target_user_ids and context.user_id is not None and str(context.user_id) in target_user_ids:
        return True, "user matched explicit target"
    if allowed_roles and context.roles.intersection(allowed_roles):
        return True, "role matched target"
    if required_beta_cohorts and context.beta_cohort_keys.intersection(required_beta_cohorts):
        return True, "beta cohort matched target"
    return True, "targeting matched"


def evaluate_feature_flag(flag: FeatureFlag | None, context: FeatureFlagContext) -> FeatureFlagEvaluationResponse:
    if flag is None:
        return FeatureFlagEvaluationResponse(key="", enabled=False, reason="flag not found")
    if not flag.enabled:
        return FeatureFlagEvaluationResponse(key=flag.key, enabled=False, reason="flag globally disabled")

    matched, reason = context_matches_flag(flag, context)
    if not matched:
        return FeatureFlagEvaluationResponse(key=flag.key, enabled=False, reason=reason)

    rollout_percentage = max(0, min(100, flag.rollout_percentage))
    if rollout_percentage <= 0:
        return FeatureFlagEvaluationResponse(key=flag.key, enabled=False, reason="rollout bucket excluded")
    if rollout_percentage < 100:
        bucket = bucket_user_for_rollout(flag_key=flag.key, identity=context.identity)
        if bucket >= rollout_percentage:
            return FeatureFlagEvaluationResponse(key=flag.key, enabled=False, reason="rollout bucket excluded")
        return FeatureFlagEvaluationResponse(key=flag.key, enabled=True, reason="rollout bucket included")

    return FeatureFlagEvaluationResponse(key=flag.key, enabled=True, reason=reason)


def evaluate_feature_flags_for_context(session: Session, context: FeatureFlagContext) -> dict[str, bool]:
    evaluated: dict[str, bool] = {}
    for flag in list_feature_flags(session):
        evaluated[flag.key] = evaluate_feature_flag(flag, context).enabled
    return evaluated


def _build_roles(current_user: User | None) -> set[str]:
    if current_user is None:
        return {"guest"}

    roles = {"authenticated", current_user.subscription_tier.lower()}
    if current_user.is_admin:
        roles.add("admin")
    if current_user.is_admin or current_user.is_editor:
        roles.add("editor")
    if current_user.is_admin or current_user.is_educator:
        roles.add("educator")
    if current_user.subscription_tier.lower() == "premium":
        roles.add("premium")
    return roles


def _resolve_identity(*, request: Request, current_user: User | None) -> str:
    if current_user is not None:
        return f"user:{current_user.id}"
    reader_identifier = request.headers.get("X-Reader-Identifier")
    if reader_identifier and reader_identifier.strip():
        return reader_identifier.strip()
    return get_request_id_from_request(request) or "anonymous"


def _get_context_child_profile(
    session: Session,
    *,
    current_user: User | None,
    child_profile_id: int | None,
) -> ChildProfile | None:
    if current_user is None or child_profile_id is None:
        return None
    statement = select(ChildProfile).where(
        ChildProfile.id == child_profile_id,
        ChildProfile.user_id == current_user.id,
        ChildProfile.is_active.is_(True),
    )
    return session.exec(statement).first()
