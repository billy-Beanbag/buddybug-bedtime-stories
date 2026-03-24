from __future__ import annotations

from dataclasses import dataclass
import logging

import httpx

from app.config import (
    STORY_GENERATION_API_KEY,
    STORY_GENERATION_BASE_URL,
    STORY_GENERATION_CANDIDATE_COUNT,
    STORY_GENERATION_DEBUG,
    STORY_GENERATION_MODEL,
    STORY_GENERATION_TIMEOUT_SECONDS,
)
from app.schemas.story_pipeline_schema import StoryBrief

logger = logging.getLogger(__name__)
TARGET_MIN_WORDS = 600
TARGET_MAX_WORDS = 800
MAX_LENGTH_REPAIR_ATTEMPTS = 2
CHARACTER_CANON_LINES = [
    "Verity is a warm human mother figure.",
    "Dolly is a gentle grey dachshund with a blue collar.",
    "Daphne is a playful black-and-tan dachshund with a red collar and star tag.",
    "Buddybug is a glowing golden firefly.",
]


@dataclass(frozen=True)
class StoryGenerationCandidate:
    text: str
    source: str
    prompt: str


def _system_prompt() -> str:
    return (
        "You write polished Buddybug children's stories for ages 5-7. "
        "Write a complete story with a clear setup, one central problem, a visible comic or surprising reveal, "
        "a coherent resolution, and a warm ending. "
        "Bedtime stories must still feel like real stories with a concrete sequence of gentle visible events, not only dreamy atmosphere. "
        "Prefer 2-4 specific middle beats such as noticing a clue, greeting a tiny garden creature, finding something, helping something small, or saying goodnight to one more part of the world. "
        "Use simple natural language, short paragraphs, and at least two lines of spoken dialogue in standard double quotes. "
        "The opening must hook the child within the first two sentences, and the ending must explicitly show the problem being solved. "
        "Character canon is non-negotiable: never change a character's species, role, or identity. "
        "Do not include meta language, writing-about-writing, poetic filler, repeated beats, or long atmospheric openings. "
        "Keep the story in one continuous line of action."
    )


def _style_examples_block(story_brief: StoryBrief) -> str:
    if not story_brief.style_reference_examples:
        return "Style reference examples: none yet"
    rendered_examples: list[str] = []
    for index, example in enumerate(story_brief.style_reference_examples[:2], start=1):
        compact_example = " ".join(example.split())
        rendered_examples.append(f"Example {index}: {compact_example[:1200]}")
    return "\n".join(["Style reference examples:", *rendered_examples])


def _character_canon_block() -> str:
    return "\n".join(
        [
            "Character canon:",
            *[f"- {line}" for line in CHARACTER_CANON_LINES],
            "- Never describe Dolly as a rabbit, bunny, hare, bear, or any species other than dachshund.",
            "- Never describe Daphne as a bear, rabbit, bunny, hare, or any species other than dachshund.",
        ]
    )


def _word_count(text: str) -> int:
    return len(text.split())


def _build_length_repair_prompt(*, story_brief: StoryBrief, draft_text: str) -> str:
    current_word_count = _word_count(draft_text)
    if current_word_count < TARGET_MIN_WORDS:
        instruction = (
            f"The draft is too short at about {current_word_count} words. Expand it to between {TARGET_MIN_WORDS} and {TARGET_MAX_WORDS} words. "
            "Do not shorten it. Add one or two concrete middle beats, extra dialogue, and a fuller calm resolution while keeping the same plot."
        )
    else:
        instruction = (
            f"The draft is too long at about {current_word_count} words. Tighten it to between {TARGET_MIN_WORDS} and {TARGET_MAX_WORDS} words "
            "without losing the hook, problem, dialogue, or resolution."
        )
    return "\n".join(
        [
            "Revise the following Buddybug story so it lands within the required word-count range.",
            instruction,
            "Keep the same characters, hook, core plot, and warm bedtime tone.",
            "Do not add meta language or poetic filler.",
            "Keep exactly 5 short paragraphs.",
            "Keep or add at least two spoken lines with standard double quotes.",
            "If the story is bedtime, make sure the middle paragraphs contain concrete visible beats rather than only dreamy description.",
            "Make sure the central problem is clearly solved before the final paragraph.",
            "Return only the revised final story text.",
            "",
            "Original draft:",
            draft_text,
        ]
    )


def _request_chat_completion(
    *,
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    candidate_index: int,
    phase: str,
) -> str:
    try:
        response = client.post(
            url,
            headers=headers,
            json={
                "model": STORY_GENERATION_MODEL,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        response.raise_for_status()
    except httpx.HTTPStatusError:
        if STORY_GENERATION_DEBUG:
            logger.error(
                "Story generation request failed: status_code=%s candidate_index=%s phase=%s response_body=%s",
                response.status_code,
                candidate_index,
                phase,
                response.text,
            )
        raise
    payload = response.json()
    if STORY_GENERATION_DEBUG:
        logger.info(
            "Story generation request succeeded: status_code=%s candidate_index=%s phase=%s",
            response.status_code,
            candidate_index,
            phase,
        )
    text = _extract_chat_completion_text(payload)
    if STORY_GENERATION_DEBUG:
        logger.info(
            "Story generation response parsed: candidate_index=%s phase=%s has_text=%s text_length=%s word_count=%s",
            candidate_index,
            phase,
            bool(text.strip()),
            len(text),
            _word_count(text),
        )
    return text


def build_story_generation_prompt(story_brief: StoryBrief) -> str:
    beat_card = story_brief.beat_card
    style_titles = ", ".join(story_brief.style_reference_titles) if story_brief.style_reference_titles else "none yet"
    rules = "\n".join(f"- {rule}" for rule in story_brief.generation_rules)
    illustration_beats = "\n".join(f"- {beat}" for beat in beat_card.illustration_beats)
    return "\n".join(
        [
            f"Audience: ages {story_brief.target_age_band}",
            f"Mode: {story_brief.mode}",
            f"Tone: {story_brief.tone}",
            f"Theme: {story_brief.theme}",
            f"Setting: {story_brief.setting}",
            f"Hook type: {story_brief.hook_type}",
            f"Humour level: {story_brief.humour_level}",
            f"Tension ceiling: {story_brief.tension_ceiling}",
            f"Target word count: about {story_brief.target_word_count}",
            f"Main characters: {', '.join(story_brief.main_characters)}",
            f"Supporting characters: {', '.join(story_brief.supporting_characters) if story_brief.supporting_characters else 'none'}",
            f"Founder reference titles: {style_titles}",
            _character_canon_block(),
            _style_examples_block(story_brief),
            "Story rules:",
            rules,
            "Beat card:",
            f"- Ordinary world: {beat_card.ordinary_world}",
            f"- Inciting moment: {beat_card.inciting_moment}",
            f"- Problem escalation: {beat_card.problem_escalation}",
            f"- Comic or surprising reveal: {beat_card.comic_or_surprising_reveal}",
            f"- Turning point: {beat_card.turning_point}",
            f"- Resolution action: {beat_card.resolution_action}",
            f"- Final emotional beat: {beat_card.final_emotional_beat}",
            "Illustration beats to support:",
            illustration_beats,
            "Output requirements:",
            "- Write between 600 and 800 words.",
            "- Use exactly 5 short paragraphs.",
            "- Include at least two spoken lines with standard double quotes.",
            "- Show the central problem clearly in paragraph 1 or 2.",
            "- Show the problem being solved clearly before the final paragraph.",
            "- For bedtime stories, include 2-4 concrete visible middle beats and avoid relying on atmosphere alone.",
            "- For bedtime stories, include at least one playful, witty, or lightly surprising middle beat before the final sleepy landing.",
            "- When appropriate for a garden, path, or outdoor bedtime setting, include one or more gentle goodnight encounters with tiny creatures such as a hedgehog, worm, frog, moth, beetle, or similar safe bedtime creature.",
            "- For adventure or standard (non-bedtime) stories, include at least one clearly funny or mischievous moment that would make children giggle; avoid calm, sleepy, or soothing tones.",
            "- For adventure or standard (non-bedtime) stories, do not end with bedtime routine beats, falling asleep, yawning into bed, or whispering goodnight.",
            "- For adventure or standard (non-bedtime) stories, end with warm alert satisfaction such as pride, relief, curiosity, celebration, or eager calm after the solution.",
            "- For adventure or standard (non-bedtime) stories, lean slightly more witty, cheeky, and afternoon-readable than the bedtime lane.",
            "Output only the final story text.",
        ]
    )


def _extract_chat_completion_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()
    return ""


def generate_story_candidates_from_brief(
    story_brief: StoryBrief,
    *,
    candidate_count: int | None = None,
) -> list[StoryGenerationCandidate]:
    """Generate full-story candidates from the durable story brief when a model is configured."""
    if not STORY_GENERATION_API_KEY.strip() or not STORY_GENERATION_MODEL.strip():
        if STORY_GENERATION_DEBUG:
            logger.info(
                "Story generation live path skipped: api_key_set=%s model_set=%s",
                bool(STORY_GENERATION_API_KEY.strip()),
                bool(STORY_GENERATION_MODEL.strip()),
            )
        return []

    count = max(1, candidate_count or STORY_GENERATION_CANDIDATE_COUNT)
    prompt = build_story_generation_prompt(story_brief)
    candidates: list[StoryGenerationCandidate] = []
    url = STORY_GENERATION_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {STORY_GENERATION_API_KEY}",
        "Content-Type": "application/json",
    }

    if STORY_GENERATION_DEBUG:
        logger.info(
            "Story generation live path active: url=%s model=%s candidate_count=%s timeout_seconds=%s",
            url,
            STORY_GENERATION_MODEL,
            count,
            STORY_GENERATION_TIMEOUT_SECONDS,
        )

    with httpx.Client(timeout=STORY_GENERATION_TIMEOUT_SECONDS) as client:
        for index in range(count):
            temperature = min(1.0, 0.7 + (index * 0.1))
            text = _request_chat_completion(
                client=client,
                url=url,
                headers=headers,
                system_prompt=_system_prompt(),
                user_prompt=prompt,
                temperature=temperature,
                candidate_index=index + 1,
                phase="initial",
            )
            repair_attempt = 0
            while text and not (TARGET_MIN_WORDS <= _word_count(text) <= TARGET_MAX_WORDS) and repair_attempt < MAX_LENGTH_REPAIR_ATTEMPTS:
                repair_attempt += 1
                if STORY_GENERATION_DEBUG:
                    logger.info(
                        "Story generation length repair requested: candidate_index=%s attempt=%s current_word_count=%s target_range=%s-%s",
                        index + 1,
                        repair_attempt,
                        _word_count(text),
                        TARGET_MIN_WORDS,
                        TARGET_MAX_WORDS,
                    )
                text = _request_chat_completion(
                    client=client,
                    url=url,
                    headers=headers,
                    system_prompt=_system_prompt(),
                    user_prompt=_build_length_repair_prompt(story_brief=story_brief, draft_text=text),
                    temperature=max(0.35, temperature - 0.15),
                    candidate_index=index + 1,
                    phase=f"length_repair_{repair_attempt}",
                )
            if text and not (TARGET_MIN_WORDS <= _word_count(text) <= TARGET_MAX_WORDS):
                if STORY_GENERATION_DEBUG:
                    logger.warning(
                        "Story generation candidate rejected for length: candidate_index=%s final_word_count=%s target_range=%s-%s",
                        index + 1,
                        _word_count(text),
                        TARGET_MIN_WORDS,
                        TARGET_MAX_WORDS,
                    )
                continue
            if text:
                candidates.append(
                    StoryGenerationCandidate(
                        text=text,
                        source=f"llm_candidate_{index + 1}",
                        prompt=prompt,
                    )
                )
    return candidates
