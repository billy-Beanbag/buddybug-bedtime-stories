from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import ApiKey
from app.models.user import utc_now

API_KEY_SCHEME_PREFIX = "bbk_live"
SCOPE_SEPARATOR = ","


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def normalize_scopes(scopes: str) -> str:
    normalized_items: list[str] = []
    seen: set[str] = set()
    for item in scopes.split(SCOPE_SEPARATOR):
        scope = item.strip()
        if not scope:
            continue
        if scope not in seen:
            seen.add(scope)
            normalized_items.append(scope)
    if not normalized_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one API scope is required")
    return ", ".join(normalized_items)


def parse_scopes(scopes: str) -> set[str]:
    return {item.strip() for item in scopes.split(SCOPE_SEPARATOR) if item.strip()}


def hash_api_key(raw_api_key: str) -> str:
    return hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()


def generate_api_key_material() -> tuple[str, str]:
    prefix_suffix = secrets.token_hex(4)
    secret = secrets.token_urlsafe(24)
    key_prefix = f"{API_KEY_SCHEME_PREFIX}_{prefix_suffix}"
    raw_api_key = f"{key_prefix}_{secret}"
    return key_prefix, raw_api_key


def extract_key_prefix(raw_api_key: str) -> str:
    parts = raw_api_key.split("_", 3)
    if len(parts) != 4 or parts[0] != "bbk" or parts[1] != "live":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key format")
    return "_".join(parts[:3])


def list_api_keys(session: Session) -> list[ApiKey]:
    return list(session.exec(select(ApiKey).order_by(ApiKey.created_at.desc())).all())


def get_api_key_or_404(session: Session, key_id: int) -> ApiKey:
    api_key = session.get(ApiKey, key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return api_key


def create_api_key(
    session: Session,
    *,
    name: str,
    scopes: str,
    created_by_user_id: int | None,
    is_active: bool = True,
) -> tuple[ApiKey, str]:
    normalized_scopes = normalize_scopes(scopes)
    while True:
        key_prefix, raw_api_key = generate_api_key_material()
        existing = session.exec(select(ApiKey).where(ApiKey.key_prefix == key_prefix)).first()
        if existing is None:
            break
    api_key = ApiKey(
        name=name,
        key_prefix=key_prefix,
        key_hash=hash_api_key(raw_api_key),
        scopes=normalized_scopes,
        is_active=is_active,
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, api_key), raw_api_key


def update_api_key(
    session: Session,
    *,
    api_key: ApiKey,
    name: str | None = None,
    scopes: str | None = None,
    is_active: bool | None = None,
) -> ApiKey:
    if name is not None:
        api_key.name = name
    if scopes is not None:
        api_key.scopes = normalize_scopes(scopes)
    if is_active is not None:
        api_key.is_active = is_active
    api_key.updated_at = utc_now()
    return _persist(session, api_key)


def deactivate_api_key(session: Session, *, api_key: ApiKey) -> ApiKey:
    api_key.is_active = False
    api_key.updated_at = utc_now()
    return _persist(session, api_key)


def validate_api_key(session: Session, *, raw_api_key: str) -> ApiKey:
    key_prefix = extract_key_prefix(raw_api_key)
    api_key = session.exec(select(ApiKey).where(ApiKey.key_prefix == key_prefix)).first()
    if api_key is None or not api_key.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if not hmac.compare_digest(api_key.key_hash, hash_api_key(raw_api_key)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    api_key.last_used_at = utc_now()
    api_key.updated_at = utc_now()
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key


def require_scope(api_key: ApiKey, *, required_scope: str) -> ApiKey:
    scopes = parse_scopes(api_key.scopes)
    if required_scope not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key scope is not permitted")
    return api_key
