"""LLM-backed story idea generation (uses same API key/model as full-story generation)."""

from __future__ import annotations

import json
import logging
import re
import secrets
from typing import Any

import httpx

from app.config import (
    STORY_GENERATION_API_KEY,
    STORY_GENERATION_BASE_URL,
    STORY_GENERATION_DEBUG,
    STORY_GENERATION_MODEL,
    STORY_GENERATION_TIMEOUT_SECONDS,
)
from app.services.story_engine_data import (
    BEDTIME_ALLOWED_HOOK_KEYS,
    BEDTIME_MODE,
    STANDARD_ALLOWED_HOOK_KEYS,
)
from app.services.story_generation_service import _extract_chat_completion_text
from app.services.story_idea_generator import _series_for_characters

logger = logging.getLogger(__name__)

_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def _strip_json_fences(raw: str) -> str:
    m = _JSON_FENCE.match(raw.strip())
    return m.group(1).strip() if m else raw.strip()


def _normalize_hook(hook: str | None, *, mode: str) -> str:
    allowed = set(BEDTIME_ALLOWED_HOOK_KEYS if mode == BEDTIME_MODE else STANDARD_ALLOWED_HOOK_KEYS)
    key = (hook or "").strip()
    if key in allowed:
        return key
    lowered = key.casefold().replace(" ", "_")
    for a in allowed:
        if a == lowered:
            return a
    return "gentle_problem" if mode == BEDTIME_MODE else "unexpected_discovery"


def _split_characters(raw: str | None, *, allowed: set[str]) -> list[str]:
    if not raw:
        return []
    names: list[str] = []
    for part in raw.replace(" and ", ",").split(","):
        name = part.strip()
        if not name:
            continue
        canon = next((a for a in allowed if a.casefold() == name.casefold()), None)
        if canon:
            names.append(canon)
    return names


def _build_user_prompt(
    *,
    count: int,
    age_band: str,
    content_lane_key: str,
    resolved_tone: str,
    mode: str,
    available_characters: list[str],
    batch_nonce: str,
    exclude_premise_lines: list[str],
) -> str:
    allowed_hooks = BEDTIME_ALLOWED_HOOK_KEYS if mode == BEDTIME_MODE else STANDARD_ALLOWED_HOOK_KEYS
    mode_label = "bedtime (calm, concrete, gentle — still a real plot)" if mode == BEDTIME_MODE else (
        "playful adventure (funny, energetic, mischief welcome — not sleepy)"
    )
    chars = ", ".join(available_characters) if available_characters else "Verity, Dolly, Daphne, Buddybug"
    lines: list[str] = [
            f"Generate exactly {count} distinct Buddybug story IDEAS (not full stories).",
            f"Target audience age band: {age_band}. Content lane key: {content_lane_key}.",
            f"Story mode: {mode_label}.",
            f"Tone to reflect in theme/feeling fields: {resolved_tone}.",
            f"Freshness batch token: {batch_nonce}. This batch must feel different from prior batches.",
            "",
            "Character canon (do not change species or roles):",
            "- Verity: warm human mother figure.",
            "- Dolly: gentle grey dachshund, blue collar.",
            "- Daphne: playful black-and-tan dachshund, red collar, gold star tag.",
            "- Buddybug: small glowing golden firefly guardian.",
            f"Only use names from this active roster: {chars}.",
            "",
            f"Each idea's hook_type MUST be one of exactly: {', '.join(allowed_hooks)}.",
            "",
            "Rules:",
            "- Premise = ONE vivid sentence a writer could expand (specific problem or comic situation).",
            "- Titles short (under 60 chars), no colon subtitles.",
            "- No duplicate premises; vary settings and problems across the batch.",
            "- Do not mention 'AI', 'story idea', or meta writing language.",
    ]
    if exclude_premise_lines:
        lines.append("")
        lines.append(
            "Do not repeat or lightly rephrase these premises already used in this lane (invent new problems):",
        )
        for ex in exclude_premise_lines:
            lines.append(f"- {ex}")
    lines.extend(
        [
            "",
            'Return ONLY valid JSON with this shape (no markdown outside the JSON):',
            '{"ideas":[{"title":"...","premise":"...","hook_type":"missing_item",'
            '"setting":"short place phrase","theme":"short","bedtime_feeling":"short",'
            '"main_characters":"Name, Name","supporting_characters":"Name or null"}]}',
        ]
    )
    return "\n".join(lines)


def try_generate_llm_idea_payloads(
    *,
    count: int,
    age_band: str,
    content_lane_key: str,
    resolved_tone: str,
    mode: str,
    available_characters: list[str],
    exclude_premises_normalized: set[str] | None = None,
    exclude_premise_hints: tuple[str, ...] | None = None,
) -> list[dict[str, Any]] | None:
    """Call chat completions; return normalized payloads or None to trigger curated fallback."""
    if not STORY_GENERATION_API_KEY.strip() or not STORY_GENERATION_MODEL.strip():
        return None

    system = (
        "You output only compact JSON for a children's book editorial tool. "
        "No markdown fences, no commentary before or after the JSON object."
    )
    batch_nonce = secrets.token_hex(5)
    exclude_lines = list(exclude_premise_hints)[:35] if exclude_premise_hints else []
    user = _build_user_prompt(
        count=count,
        age_band=age_band,
        content_lane_key=content_lane_key,
        resolved_tone=resolved_tone,
        mode=mode,
        available_characters=available_characters,
        batch_nonce=batch_nonce,
        exclude_premise_lines=exclude_lines,
    )
    url = STORY_GENERATION_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {STORY_GENERATION_API_KEY}",
        "Content-Type": "application/json",
    }
    base_body: dict[str, Any] = {
        "model": STORY_GENERATION_MODEL,
        "temperature": 0.98,
        "max_tokens": min(4000, 400 + count * 350),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    try:
        with httpx.Client(timeout=STORY_GENERATION_TIMEOUT_SECONDS) as client:
            body = {**base_body, "response_format": {"type": "json_object"}}
            response = client.post(url, headers=headers, json=body)
            if response.status_code >= 400 and "response_format" in body:
                # Non-OpenAI or older gateway: retry without json_object mode.
                response = client.post(url, headers=headers, json=base_body)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        logger.exception("LLM story idea generation request failed")
        return None

    text = _extract_chat_completion_text(payload)
    if not text:
        if STORY_GENERATION_DEBUG:
            logger.warning("LLM story idea generation returned empty content")
        return None

    try:
        data = json.loads(_strip_json_fences(text))
    except json.JSONDecodeError:
        logger.warning("LLM story idea generation returned non-JSON; first 200 chars: %s", text[:200])
        return None

    raw_ideas = data.get("ideas")
    if not isinstance(raw_ideas, list) or not raw_ideas:
        return None

    allowed_names = set(available_characters) if available_characters else {
        "Verity",
        "Dolly",
        "Daphne",
        "Buddybug",
    }
    out: list[dict[str, Any]] = []
    for item in raw_ideas:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        premise = str(item.get("premise") or "").strip()
        if not title or not premise:
            continue
        ex_norm = exclude_premises_normalized or set()
        if premise.casefold() in ex_norm:
            continue
        hook_type = _normalize_hook(str(item.get("hook_type") or ""), mode=mode)
        setting = str(item.get("setting") or "garden path").strip() or "garden path"
        theme = str(item.get("theme") or "friendship").strip() or "friendship"
        bedtime_feeling = str(item.get("bedtime_feeling") or "cozy").strip() or "cozy"
        mains = _split_characters(str(item.get("main_characters") or ""), allowed=allowed_names)
        supports = _split_characters(str(item.get("supporting_characters") or ""), allowed=allowed_names)
        if len(mains) < 1 and available_characters:
            mains = [available_characters[0]]
            if len(available_characters) > 1 and len(mains) < 2:
                mains.append(available_characters[1])
        if len(mains) < 1:
            mains = ["Buddybug"]
        main_set = set(mains)
        supports = [s for s in supports if s not in main_set][:3]
        series_key, series_title = _series_for_characters(mains, supports)
        out.append(
            {
                "title": title[:120],
                "premise": premise[:500],
                "hook_type": hook_type,
                "age_band": age_band,
                "content_lane_key": content_lane_key,
                "tone": resolved_tone,
                "setting": setting[:200],
                "theme": theme[:120],
                "bedtime_feeling": bedtime_feeling[:120],
                "main_characters": ", ".join(mains),
                "supporting_characters": ", ".join(supports) if supports else None,
                "series_key": series_key,
                "series_title": series_title,
                "estimated_minutes": 7 if mode == BEDTIME_MODE else 6,
                "status": "idea_pending",
                "generation_source": "llm_generated_idea",
            }
        )
        if len(out) >= count:
            break

    if out:
        logger.info("story_idea_llm: parsed %s ideas (requested %s)", len(out), count)
    return out[:count] if out else None
