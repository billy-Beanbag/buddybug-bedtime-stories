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
    STORY_IDEA_GENERATION_USE_LLM,
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
    return "unexpected_discovery"


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
    editorial_guidance_lines: list[str],
) -> str:
    allowed_hooks = BEDTIME_ALLOWED_HOOK_KEYS if mode == BEDTIME_MODE else STANDARD_ALLOWED_HOOK_KEYS
    mode_label = "plot-led bedtime (cozy and sleepy by the ending, but lively and engaging on the way)" if mode == BEDTIME_MODE else (
        "afternoon adventure (witty, cheeky, energetic, plot-led, mischief welcome — not sleepy, not bedtime)"
    )
    chars = ", ".join(available_characters) if available_characters else "Verity, Dolly, Daphne, Buddybug"
    lines: list[str] = [
            f"Generate exactly {count} distinct Buddybug story IDEAS (not full stories).",
            f"Target audience age band: {age_band}. Content lane key: {content_lane_key}.",
            f"Story mode: {mode_label}.",
            f"Tone to reflect in theme/feeling fields: {resolved_tone}.",
            f"Freshness batch token: {batch_nonce}. This batch must feel different from prior batches.",
            "",
            "The strongest ideas should feel like real little children's stories, not abstract editorial placeholders.",
            "Each premise must suggest a specific first scene, a recognisable child situation, and a satisfying direction the story could take.",
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
            "- Premise = ONE or TWO vivid sentences a writer could expand immediately into a real story scene.",
            "- Prefer real-world child situations: losing track of something meaningful, misunderstanding what was seen, a plan becoming unexpectedly funny, an odd discovery, a bedtime ritual taking an unexpected turn, a pet or tiny creature behaviour that starts a story, a game or promise that changes shape, or a small emotional/social moment children actually recognise.",
            "- The premise should sound like something a parent could read and instantly picture as a genuine story, not a template.",
            "- Do not write generic placeholders such as 'something is not quite right', 'a small problem appears', 'they decide to fix it', 'a funny problem to solve', or 'a clue in the wrong place' unless the concrete thing is named and vivid.",
            "- The opening image should be concrete: what is seen, found, heard, hidden, misplaced, mistaken, promised, followed, borrowed, discovered, or interrupted?",
            "- Avoid meaningless conflict. The story should move because something specific is happening, not because the premise says there is a problem.",
            "- Titles short (under 60 chars), no colon subtitles.",
            "- No duplicate premises; vary settings, story movement, and emotional payoffs across the batch.",
            "- Do not mention 'AI', 'story idea', or meta writing language.",
    ]
    if mode == BEDTIME_MODE:
        lines.extend(
            [
                "- Bedtime ideas should feel calm but real: curiosity, ritual, misread signs, finding, noticing, helping, following, hiding, borrowing, waiting, wondering, or gently putting something right are all welcome.",
                "- Bedtime does not have to mean a repair job. It can begin with a discovery, question, promise, search, or strange little observation.",
                "- Bedtime ideas should still include one playful, funny, or surprising middle turn before landing in a sleepy, reassuring, clearly settled conclusion.",
                "- Prefer hook types like unexpected_discovery, misunderstanding, tiny_creature_problem, or missing_item unless another hook is truly more vivid.",
                "- Use gentle_problem only when the premise is still highly specific and visual, not vague.",
            ]
        )
    else:
        lines.extend(
            [
                "- Adventure ideas must not end with going to bed, falling asleep, bedtime routine beats, or sleepy goodnight framing.",
                "- Adventure ideas should feel witty, cheeky, and engaging enough for an afternoon read, with a stronger comic or mischievous turn than bedtime stories.",
                "- Aim for a warm but alert ending: proud, relieved, excited, curious, or cheerfully satisfied.",
                "- Adventure ideas should begin with a concrete lively situation, not a generic statement that a problem exists.",
            ]
        )
    if exclude_premise_lines:
        lines.append("")
        lines.append(
            "Do not repeat or lightly rephrase these premises already used in this lane (invent new problems):",
        )
        for ex in exclude_premise_lines:
            lines.append(f"- {ex}")
    if editorial_guidance_lines:
        lines.append("")
        lines.append("Approved parent suggestion guidance to learn from when inventing fresh ideas:")
        for line in editorial_guidance_lines[:12]:
            lines.append(f"- {line}")
        lines.extend(
            [
                "- Use this guidance as inspiration for tone, emotional payoff, and preferred story shape.",
                "- Do not copy these suggestions verbatim; transform them into fresh, distinct new premises.",
            ]
        )
    lines.extend(
        [
            "",
            "Examples of the level of specificity wanted:",
            "- GOOD: \"Daphne hides her gold star tag for safekeeping during a pirate game and then cannot remember which of her six 'treasure caves' she chose.\"",
            '- GOOD: "Buddybug notices that every snail in the garden is somehow heading toward the same flowerpot, and Dolly becomes certain they know something important."',
            '- BAD: "Something in the bedroom is not quite right, so the friends try to fix it."',
            '- BAD: "A clue appears in the wrong place and causes a little problem."',
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
    editorial_guidance: tuple[str, ...] | None = None,
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
        editorial_guidance_lines=list(editorial_guidance or ()),
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


def try_normalize_parent_suggestion_to_idea_payload(
    *,
    title: str | None,
    brief: str,
    desired_outcome: str | None,
    inspiration_notes: str | None,
    avoid_notes: str | None,
    age_band: str,
    content_lane_key: str,
    resolved_tone: str,
    mode: str,
    available_characters: list[str],
) -> dict[str, Any] | None:
    """Convert one approved parent suggestion into a structured StoryIdea-like payload."""
    if (
        not STORY_IDEA_GENERATION_USE_LLM
        or not STORY_GENERATION_API_KEY.strip()
        or not STORY_GENERATION_MODEL.strip()
    ):
        return None

    allowed_hooks = BEDTIME_ALLOWED_HOOK_KEYS if mode == BEDTIME_MODE else STANDARD_ALLOWED_HOOK_KEYS
    chars = ", ".join(available_characters) if available_characters else "Verity, Dolly, Daphne, Buddybug"
    mode_label = "bedtime" if mode == BEDTIME_MODE else "adventure"
    system = (
        "You output only compact JSON for a children's book editorial tool. "
        "No markdown fences, no commentary before or after the JSON object."
    )
    user = "\n".join(
        [
            "Convert this approved parent suggestion into ONE structured Buddybug story idea.",
            f"Age band: {age_band}. Content lane key: {content_lane_key}. Mode: {mode_label}.",
            f"Tone: {resolved_tone}.",
            "",
            "The output must preserve the parent's concrete scenario, but normalize it into fields a writer can use.",
            "Do not produce abstract filler, placeholder language, or meta-writing phrasing.",
            "Do not use the submitting child's name as a story character unless it already matches the canonical Buddybug roster.",
            f"Only use names from this roster: {chars}.",
            f"hook_type must be one of: {', '.join(allowed_hooks)}.",
            "",
            "Field rules:",
            "- title: short, vivid, publishable Buddybug-style title",
            "- premise: one or two concrete sentences grounded in the parent's scenario",
            "- setting: short place phrase only",
            "- theme: short emotional/theme phrase only",
            "- bedtime_feeling: short ending feeling phrase only",
            "- main_characters: one or two roster names, comma-separated",
            "- supporting_characters: zero to three roster names, comma-separated, excluding main characters",
            "",
            "Parent suggestion:",
            f"- title: {(title or '').strip() or '(none)'}",
            f"- brief: {brief.strip()}",
            f"- desired_outcome: {(desired_outcome or '').strip() or '(none)'}",
            f"- inspiration_notes: {(inspiration_notes or '').strip() or '(none)'}",
            f"- avoid_notes: {(avoid_notes or '').strip() or '(none)'}",
            "",
            'Return ONLY valid JSON with this shape:',
            '{"idea":{"title":"...","premise":"...","hook_type":"missing_item","setting":"...","theme":"...","bedtime_feeling":"...","main_characters":"Name, Name","supporting_characters":"Name"}}',
        ]
    )
    url = STORY_GENERATION_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {STORY_GENERATION_API_KEY}",
        "Content-Type": "application/json",
    }
    base_body: dict[str, Any] = {
        "model": STORY_GENERATION_MODEL,
        "temperature": 0.45,
        "max_tokens": 700,
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
                response = client.post(url, headers=headers, json=base_body)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        logger.exception("LLM parent suggestion normalization failed")
        return None

    text = _extract_chat_completion_text(payload)
    if not text:
        if STORY_GENERATION_DEBUG:
            logger.warning("LLM parent suggestion normalization returned empty content")
        return None

    try:
        data = json.loads(_strip_json_fences(text))
    except json.JSONDecodeError:
        logger.warning("LLM parent suggestion normalization returned non-JSON; first 200 chars: %s", text[:200])
        return None

    item = data.get("idea")
    if not isinstance(item, dict):
        return None

    allowed_names = set(available_characters) if available_characters else {
        "Verity",
        "Dolly",
        "Daphne",
        "Buddybug",
    }
    parsed_title = str(item.get("title") or "").strip()
    parsed_premise = str(item.get("premise") or "").strip()
    if not parsed_title or not parsed_premise:
        return None
    mains = _split_characters(str(item.get("main_characters") or ""), allowed=allowed_names)
    supports = _split_characters(str(item.get("supporting_characters") or ""), allowed=allowed_names)
    if len(mains) < 1 and available_characters:
        mains = [available_characters[0]]
        if len(available_characters) > 1:
            mains.append(available_characters[1])
    if len(mains) < 1:
        mains = ["Buddybug", "Dolly"]
    if len(mains) > 2:
        mains = mains[:2]
    main_set = set(mains)
    supports = [name for name in supports if name not in main_set][:3]
    series_key, series_title = _series_for_characters(mains, supports)
    return {
        "title": parsed_title[:120],
        "premise": parsed_premise[:500],
        "hook_type": _normalize_hook(str(item.get("hook_type") or ""), mode=mode),
        "age_band": age_band,
        "content_lane_key": content_lane_key,
        "tone": resolved_tone,
        "setting": (str(item.get("setting") or "garden path").strip() or "garden path")[:200],
        "theme": (str(item.get("theme") or "friendship").strip() or "friendship")[:120],
        "bedtime_feeling": (str(item.get("bedtime_feeling") or "proud, reassured, and calm").strip() or "proud, reassured, and calm")[:120],
        "main_characters": ", ".join(mains),
        "supporting_characters": ", ".join(supports) if supports else None,
        "series_key": series_key,
        "series_title": series_title,
        "estimated_minutes": 7 if mode == BEDTIME_MODE else 6,
        "status": "idea_pending",
        "generation_source": "parent_suggestion_llm",
    }
