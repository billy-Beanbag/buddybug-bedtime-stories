from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import ChildProfile
from app.services.i18n_service import normalize_language
from app.services.narration_service import get_voice_by_key
from app.services.storage_service import (
    build_child_name_audio_path,
    get_asset_url,
    get_local_asset_path,
    save_bytes,
)
from app.services.tts_adapter import build_tts_adapter


@dataclass(frozen=True)
class ChildNameNarrationAsset:
    child_profile_id: int
    voice_key: str
    language: str
    source_text: str
    snippet_type: str
    audio_url: str
    duration_seconds: int | None
    provider: str
    cached: bool


def _normalize_name_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "child"


def _resolve_source_text(child: ChildProfile, source_text: str | None) -> str:
    resolved = (source_text or child.display_name).strip()
    if not resolved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Child name text is required")
    return resolved


def ensure_child_name_narration_asset(
    session: Session,
    *,
    child_profile_id: int,
    voice_key: str,
    language: str,
    source_text: str | None = None,
    snippet_type: str = "name_only",
    replace_existing: bool = False,
) -> ChildNameNarrationAsset:
    child = session.get(ChildProfile, child_profile_id)
    if child is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child profile not found")

    voice = get_voice_by_key(session, voice_key)
    normalized_language = normalize_language(language or child.language)
    if voice.language != normalized_language:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voice language does not match request")

    resolved_source_text = _resolve_source_text(child, source_text)
    name_key = _normalize_name_key(resolved_source_text)
    snippet_key = _normalize_name_key(snippet_type)
    cache_hash = hashlib.sha256(f"{normalized_language}:{voice.key}:{snippet_key}:{resolved_source_text}".encode("utf-8")).hexdigest()[:16]
    adapter = build_tts_adapter()
    guessed_extension = adapter.preferred_file_extension(voice)
    precomputed_path = build_child_name_audio_path(
        child_profile_id=child.id,
        voice_key=voice.key,
        language=normalized_language,
        snippet_type=f"{snippet_key}-{name_key}",
        cache_key=cache_hash,
        extension=guessed_extension,
    )
    local_path = get_local_asset_path(precomputed_path)
    if local_path.exists() and not replace_existing:
        return ChildNameNarrationAsset(
            child_profile_id=child.id,
            voice_key=voice.key,
            language=normalized_language,
            source_text=resolved_source_text,
            snippet_type=snippet_type,
            audio_url=get_asset_url(precomputed_path),
            duration_seconds=None,
            provider="cached",
            cached=True,
        )

    result = adapter.generate_speech(text=resolved_source_text, voice=voice, language=normalized_language)
    asset_path = save_bytes(
        build_child_name_audio_path(
            child_profile_id=child.id,
            voice_key=voice.key,
            language=normalized_language,
            snippet_type=f"{snippet_key}-{name_key}",
            cache_key=cache_hash,
            extension=result.file_extension,
        ),
        result.audio_bytes,
    )
    return ChildNameNarrationAsset(
        child_profile_id=child.id,
        voice_key=voice.key,
        language=normalized_language,
        source_text=resolved_source_text,
        snippet_type=snippet_type,
        audio_url=get_asset_url(asset_path),
        duration_seconds=result.duration_seconds,
        provider=result.provider,
        cached=False,
    )
