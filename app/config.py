import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return int(raw_value)


def _normalize_cors_origin(value: str) -> str:
    """Strip whitespace and optional wrapping quotes (common when pasting into dashboards)."""
    origin = value.strip()
    if len(origin) >= 2 and origin[0] == origin[-1] and origin[0] in {'"', "'"}:
        origin = origin[1:-1].strip()
    return origin


def _parse_cors_allow_origins(raw: str) -> list[str]:
    origins: list[str] = []
    for part in raw.split(","):
        o = _normalize_cors_origin(part)
        if o:
            origins.append(o)
    return origins


def _parse_cors_allow_origin_regex(raw: str | None) -> str | None:
    if raw is None or not raw.strip():
        return None
    pattern = raw.strip()
    if len(pattern) >= 2 and pattern.startswith("/") and pattern.endswith("/"):
        pattern = pattern[1:-1].strip()
    return pattern or None


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    debug: bool
    log_level: str
    enable_request_id_logging: bool
    rate_limit_enabled: bool
    auth_rate_limit_per_minute: int
    billing_rate_limit_per_minute: int
    database_url: str
    secret_key: str
    access_token_expire_minutes: int
    algorithm: str
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_id_premium_monthly: str
    stripe_success_url: str
    stripe_cancel_url: str
    terms_version: str
    privacy_policy_version: str
    cors_allow_origins: list[str]
    cors_allow_origin_regex: str | None
    storage_backend: str
    storage_local_base_path: str
    storage_public_base_url: str
    s3_bucket_name: str
    s3_region: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_endpoint_url: str
    story_generation_api_key: str
    story_generation_model: str
    story_generation_base_url: str
    story_generation_timeout_seconds: int
    story_generation_candidate_count: int
    story_generation_debug: bool
    story_generation_require_live: bool
    story_idea_generation_use_llm: bool
    illustration_generation_provider: str
    illustration_generation_api_key: str
    illustration_generation_model: str
    illustration_generation_base_url: str
    illustration_generation_timeout_seconds: int
    illustration_generation_debug: bool


def get_settings() -> Settings:
    default_database_url = f"sqlite:///{PROJECT_ROOT / 'buddybug.db'}"
    default_cors_origins = "http://127.0.0.1:3000,http://localhost:3000"
    raw_illustration_generation_model = os.getenv("ILLUSTRATION_GENERATION_MODEL", "gpt-image-1.5").strip()
    if raw_illustration_generation_model == "gpt-image-1":
        raw_illustration_generation_model = "gpt-image-1.5"
    return Settings(
        app_name=os.getenv("APP_NAME", "Buddybug Storylight Backend"),
        app_env=os.getenv("APP_ENV", "development"),
        debug=_get_bool_env("DEBUG", True),
        log_level=os.getenv("LOG_LEVEL", "DEBUG" if _get_bool_env("DEBUG", True) else "INFO"),
        enable_request_id_logging=_get_bool_env("ENABLE_REQUEST_ID_LOGGING", True),
        rate_limit_enabled=_get_bool_env("RATE_LIMIT_ENABLED", True),
        auth_rate_limit_per_minute=_get_int_env("AUTH_RATE_LIMIT_PER_MINUTE", 10),
        billing_rate_limit_per_minute=_get_int_env("BILLING_RATE_LIMIT_PER_MINUTE", 20),
        database_url=os.getenv("DATABASE_URL", default_database_url),
        secret_key=os.getenv("SECRET_KEY", "buddybug-dev-secret-key-change-me"),
        access_token_expire_minutes=_get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 10080),
        algorithm=os.getenv("ALGORITHM", "HS256"),
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        stripe_price_id_premium_monthly=os.getenv("STRIPE_PRICE_ID_PREMIUM_MONTHLY", ""),
        stripe_success_url=os.getenv(
            "STRIPE_SUCCESS_URL",
            "http://localhost:3000/profile?billing=success",
        ),
        stripe_cancel_url=os.getenv(
            "STRIPE_CANCEL_URL",
            "http://localhost:3000/profile?billing=cancel",
        ),
        terms_version=os.getenv("TERMS_VERSION", "2026-01"),
        privacy_policy_version=os.getenv("PRIVACY_POLICY_VERSION", "2026-01"),
        cors_allow_origins=_parse_cors_allow_origins(os.getenv("CORS_ALLOW_ORIGINS", default_cors_origins)),
        cors_allow_origin_regex=_parse_cors_allow_origin_regex(os.getenv("CORS_ALLOW_ORIGIN_REGEX")),
        storage_backend=os.getenv("STORAGE_BACKEND", "local"),
        storage_local_base_path=os.getenv("STORAGE_LOCAL_BASE_PATH", str(PROJECT_ROOT / "storage")),
        storage_public_base_url=os.getenv("STORAGE_PUBLIC_BASE_URL", "http://localhost:8000"),
        s3_bucket_name=os.getenv("S3_BUCKET_NAME", ""),
        s3_region=os.getenv("S3_REGION", ""),
        s3_access_key_id=os.getenv("S3_ACCESS_KEY_ID", ""),
        s3_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY", ""),
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL", ""),
        story_generation_api_key=os.getenv("STORY_GENERATION_API_KEY", ""),
        story_generation_model=os.getenv("STORY_GENERATION_MODEL", ""),
        story_generation_base_url=os.getenv("STORY_GENERATION_BASE_URL", "https://api.openai.com/v1"),
        story_generation_timeout_seconds=_get_int_env("STORY_GENERATION_TIMEOUT_SECONDS", 45),
        story_generation_candidate_count=_get_int_env("STORY_GENERATION_CANDIDATE_COUNT", 2),
        story_generation_debug=_get_bool_env("STORY_GENERATION_DEBUG", False),
        story_generation_require_live=_get_bool_env("STORY_GENERATION_REQUIRE_LIVE", False),
        story_idea_generation_use_llm=_get_bool_env("STORY_IDEA_GENERATION_USE_LLM", True),
        illustration_generation_provider=os.getenv("ILLUSTRATION_GENERATION_PROVIDER", "mock"),
        illustration_generation_api_key=os.getenv("ILLUSTRATION_GENERATION_API_KEY", ""),
        illustration_generation_model=raw_illustration_generation_model,
        illustration_generation_base_url=os.getenv("ILLUSTRATION_GENERATION_BASE_URL", "https://api.openai.com/v1"),
        illustration_generation_timeout_seconds=_get_int_env("ILLUSTRATION_GENERATION_TIMEOUT_SECONDS", 60),
        illustration_generation_debug=_get_bool_env("ILLUSTRATION_GENERATION_DEBUG", False),
    )


settings = get_settings()
APP_NAME = settings.app_name
APP_ENV = settings.app_env
DEBUG = settings.debug
LOG_LEVEL = settings.log_level
ENABLE_REQUEST_ID_LOGGING = settings.enable_request_id_logging
RATE_LIMIT_ENABLED = settings.rate_limit_enabled
AUTH_RATE_LIMIT_PER_MINUTE = settings.auth_rate_limit_per_minute
BILLING_RATE_LIMIT_PER_MINUTE = settings.billing_rate_limit_per_minute
DATABASE_URL = settings.database_url
SECRET_KEY = settings.secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
ALGORITHM = settings.algorithm
STRIPE_SECRET_KEY = settings.stripe_secret_key
STRIPE_WEBHOOK_SECRET = settings.stripe_webhook_secret
STRIPE_PRICE_ID_PREMIUM_MONTHLY = settings.stripe_price_id_premium_monthly
STRIPE_SUCCESS_URL = settings.stripe_success_url
STRIPE_CANCEL_URL = settings.stripe_cancel_url
TERMS_VERSION = settings.terms_version
PRIVACY_POLICY_VERSION = settings.privacy_policy_version
CORS_ALLOW_ORIGINS = settings.cors_allow_origins
CORS_ALLOW_ORIGIN_REGEX = settings.cors_allow_origin_regex
STORAGE_BACKEND = settings.storage_backend
STORAGE_LOCAL_BASE_PATH = settings.storage_local_base_path
STORAGE_PUBLIC_BASE_URL = settings.storage_public_base_url
S3_BUCKET_NAME = settings.s3_bucket_name
S3_REGION = settings.s3_region
S3_ACCESS_KEY_ID = settings.s3_access_key_id
S3_SECRET_ACCESS_KEY = settings.s3_secret_access_key
S3_ENDPOINT_URL = settings.s3_endpoint_url
STORY_GENERATION_API_KEY = settings.story_generation_api_key
STORY_GENERATION_MODEL = settings.story_generation_model
STORY_GENERATION_BASE_URL = settings.story_generation_base_url
STORY_GENERATION_TIMEOUT_SECONDS = settings.story_generation_timeout_seconds
STORY_GENERATION_CANDIDATE_COUNT = settings.story_generation_candidate_count
STORY_GENERATION_DEBUG = settings.story_generation_debug
STORY_GENERATION_REQUIRE_LIVE = settings.story_generation_require_live
STORY_IDEA_GENERATION_USE_LLM = settings.story_idea_generation_use_llm
ILLUSTRATION_GENERATION_PROVIDER = settings.illustration_generation_provider
ILLUSTRATION_GENERATION_API_KEY = settings.illustration_generation_api_key
ILLUSTRATION_GENERATION_MODEL = settings.illustration_generation_model
ILLUSTRATION_GENERATION_BASE_URL = settings.illustration_generation_base_url
ILLUSTRATION_GENERATION_TIMEOUT_SECONDS = settings.illustration_generation_timeout_seconds
ILLUSTRATION_GENERATION_DEBUG = settings.illustration_generation_debug