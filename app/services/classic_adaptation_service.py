from __future__ import annotations

from dataclasses import dataclass
import logging
import re

import httpx
from sqlmodel import Session

from app.config import (
    STORY_GENERATION_API_KEY,
    STORY_GENERATION_BASE_URL,
    STORY_GENERATION_DEBUG,
    STORY_GENERATION_MODEL,
    STORY_GENERATION_TIMEOUT_SECONDS,
)
from app.models import ClassicSource
from app.services.classic_adaptation_validation import (
    VALIDATION_REJECTED,
    ClassicAdaptationValidationResult,
    validate_classic_adaptation_output,
)
from app.services.classic_prompt_templates import (
    CLASSIC_CAMEO_CHARACTER_NAMES,
    ClassicAdaptationStructuredResponse,
    ClassicCameoInsertionSummaryItem,
    ClassicSceneSeedNote,
    build_classic_adaptation_system_prompt,
    build_classic_adaptation_user_prompt,
    parse_classic_adaptation_response_text,
    render_adaptation_notes,
    render_cameo_insertions_summary,
    render_scene_seed_notes_json,
    validate_classic_adaptation_intensity,
)

logger = logging.getLogger(__name__)

SETTING_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("bears' forest cottage", ("bear", "porridge", "chair", "cottage", "little house")),
    ("woodland path", ("forest", "path", "woods", "trail")),
    ("grandmother's cottage", ("grandmamma", "grandmother", "wolf", "wood", "village")),
    ("royal bedchamber", ("princess", "pea", "queen", "mattresses", "bedstead")),
    ("shoemaker's workshop", ("shoemaker", "shoe", "shoes", "leather", "table")),
    ("farmyard and riverside", ("duck", "duckling", "farm-house", "farmyard", "river")),
    ("fairytale meadow", ("meadow", "field", "grass", "hill")),
    ("storybook cottage bedroom", ("bed", "bedroom", "pillow", "quilt")),
]
MOOD_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("peaceful", ("quiet", "peaceful", "gentle", "soft")),
    ("gently curious", ("curious", "wonder", "noticed", "peeked")),
    ("warmly magical", ("glow", "shimmer", "sparkle", "magic")),
    ("tense but child-safe", ("surprised", "worried", "startled", "alarmed")),
]


@dataclass(frozen=True)
class ClassicAdaptationResult:
    structured_output: ClassicAdaptationStructuredResponse
    adaptation_intensity: str
    validation: ClassicAdaptationValidationResult
    source: str
    used_fallback: bool

    @property
    def adapted_title(self) -> str:
        return self.structured_output.adaptedTitle.strip()

    @property
    def adapted_text(self) -> str:
        return self.structured_output.adaptedText.strip()

    @property
    def adaptation_notes(self) -> str:
        return render_adaptation_notes(self.structured_output.adaptationNotes)

    @property
    def cameo_insertions_summary(self) -> str:
        return render_cameo_insertions_summary(self.structured_output.cameoInsertionsSummary)

    @property
    def scene_seed_notes_json(self) -> str:
        return render_scene_seed_notes_json(self.structured_output.sceneSeedNotes)

    @property
    def validation_status(self) -> str:
        return self.validation.status

    @property
    def validation_warnings(self) -> list[str]:
        return list(self.validation.warnings)

    @property
    def editor_notes(self) -> str:
        lines = [
            f"Adaptation source: {self.source}.",
            f"Adaptation intensity: {self.adaptation_intensity}.",
            f"Validation status: {self.validation.status}.",
        ]
        if self.used_fallback:
            lines.append("Fallback adaptation was used to preserve the classic safely.")
        if self.validation.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in self.validation.warnings)
        if self.validation.errors:
            lines.append("Errors:")
            lines.extend(f"- {error}" for error in self.validation.errors)
        return "\n".join(lines)


def _extract_chat_completion_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        return "\n".join(part for part in text_parts if part).strip()
    return ""


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _split_paragraphs(source_text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", source_text) if part.strip()]
    if paragraphs:
        return paragraphs
    sentences = _split_sentences(source_text.strip())
    paragraphs = []
    current: list[str] = []
    for sentence in sentences:
        current.append(sentence)
        if len(" ".join(current).split()) >= 90:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs or [source_text.strip()]


def _choose_scene_count(paragraphs: list[str], *, min_scenes: int, max_scenes: int) -> int:
    if not paragraphs:
        return min_scenes
    return max(min_scenes, min(max_scenes, len(paragraphs)))


def _chunk_paragraphs(paragraphs: list[str], scene_count: int) -> list[str]:
    if not paragraphs:
        return []
    chunked: list[str] = []
    for index in range(scene_count):
        start = (index * len(paragraphs)) // scene_count
        end = ((index + 1) * len(paragraphs)) // scene_count
        chunk = " ".join(paragraphs[start:end]).strip()
        if chunk:
            chunked.append(chunk)
    return chunked or [" ".join(paragraphs).strip()]


def _detect_scene_characters(text: str) -> list[str]:
    found = [name for name in CLASSIC_CAMEO_CHARACTER_NAMES if re.search(rf"\b{re.escape(name)}\b", text)]
    return found


def _infer_setting(text: str) -> str:
    lowered = text.casefold()
    for label, keywords in SETTING_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return label
    return "storybook fairytale setting"


def _infer_mood(text: str) -> str:
    lowered = text.casefold()
    for label, keywords in MOOD_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return label
    return "warm bedtime calm"


def _excerpt_anchor(text: str) -> str:
    sentence = _split_sentences(text)[0] if _split_sentences(text) else text.strip()
    sentence = re.sub(r"\s+", " ", sentence).strip()
    return sentence[:180].rstrip()


def _key_visual_action(text: str) -> str:
    sentence = _excerpt_anchor(text)
    return sentence or "preserve the clearest iconic action from this part of the classic"


def derive_classic_scene_seed_notes(
    *,
    title: str,
    adapted_text: str,
    min_scenes: int,
    max_scenes: int,
) -> list[ClassicSceneSeedNote]:
    paragraphs = _split_paragraphs(adapted_text)
    scene_count = _choose_scene_count(paragraphs, min_scenes=min_scenes, max_scenes=max_scenes)
    chunks = _chunk_paragraphs(paragraphs, scene_count)
    notes: list[ClassicSceneSeedNote] = []
    for index, chunk in enumerate(chunks, start=1):
        notes.append(
            ClassicSceneSeedNote(
                sceneIndex=index,
                label=f"{title} scene {index}",
                excerptAnchor=_excerpt_anchor(chunk),
                featuredCharacters=_detect_scene_characters(chunk),
                setting=_infer_setting(chunk),
                mood=_infer_mood(chunk),
                keyVisualAction=_key_visual_action(chunk),
                illustrationNotes="Preserve the iconic classic action and include Buddybug cameo characters only if this scene text truly contains them.",
            )
        )
    return notes


def _fallback_cameo_lines(adaptation_intensity: str) -> list[str]:
    intensity = validate_classic_adaptation_intensity(adaptation_intensity)
    if intensity == "minimal":
        return [
            "High above, Buddybug gave the gentlest glow, then let the old story carry on exactly as it should.",
            "For only a moment, Glowmoth added a calm shimmer and then drifted quietly out of sight.",
        ]
    if intensity == "gentle_plus":
        return [
            "High above, Buddybug gave a small golden glow, as if quietly promising that the old story was unfolding just as it should.",
            "From the edge of the path, Dolly and Daphne watched for a moment, then padded softly on without disturbing a thing.",
            "Twinklet flickered once like a tiny star, while Whisperwing drifted nearby so lightly that the classic scene stayed entirely its own.",
        ]
    return [
        "High above, Buddybug gave a small golden glow, then let the story continue exactly as it always had.",
        "For a moment, Glowmoth added the faintest soothing shimmer before the classic tale carried on unchanged.",
        "Twinklet flickered once in the hush, only as a tiny witness to the old familiar scene.",
    ]


def _fallback_structured_output(
    classic_source: ClassicSource,
    *,
    adaptation_intensity: str,
    min_scenes: int,
    max_scenes: int,
) -> ClassicAdaptationStructuredResponse:
    paragraphs = _split_paragraphs(classic_source.source_text)
    insertion_indexes: list[int] = []
    intensity = validate_classic_adaptation_intensity(adaptation_intensity)
    if intensity == "minimal":
        if len(paragraphs) >= 4:
            insertion_indexes.append(1)
    elif intensity == "gentle_plus":
        if len(paragraphs) >= 3:
            insertion_indexes.extend([1, len(paragraphs) // 2, max(len(paragraphs) - 2, 1)])
    else:
        if len(paragraphs) >= 3:
            insertion_indexes.append(1)
        if len(paragraphs) >= 6:
            insertion_indexes.append(len(paragraphs) // 2)
    insertion_indexes = sorted({index for index in insertion_indexes if 0 <= index < len(paragraphs)})

    cameo_lines = _fallback_cameo_lines(intensity)
    adapted_parts: list[str] = []
    cameo_summary_items: list[ClassicCameoInsertionSummaryItem] = []
    cameo_offset = 0
    for index, paragraph in enumerate(paragraphs):
        adapted_parts.append(paragraph)
        if index in insertion_indexes:
            cameo_line = cameo_lines[cameo_offset % len(cameo_lines)]
            adapted_parts.append(cameo_line)
            character_name = next((name for name in CLASSIC_CAMEO_CHARACTER_NAMES if name in cameo_line), "Buddybug")
            cameo_summary_items.append(
                ClassicCameoInsertionSummaryItem(
                    insertionLabel=f"classic cameo {cameo_offset + 1}",
                    approximateLocation=f"after source paragraph {index + 1}",
                    characters=[character_name],
                    reason="Adds a brief magical witness line without changing the classic plot.",
                    plotPreservationNote="The original story beat and order remain unchanged.",
                )
            )
            cameo_offset += 1

    adapted_text = "\n\n".join(part.strip() for part in adapted_parts if part.strip())
    adaptation_notes = [
        "Original plot preserved",
        "Buddybug additions kept sparse and non-intrusive",
        "No ending changes made",
    ]
    scene_seed_notes = derive_classic_scene_seed_notes(
        title=classic_source.title,
        adapted_text=adapted_text,
        min_scenes=min_scenes,
        max_scenes=max_scenes,
    )
    return ClassicAdaptationStructuredResponse(
        adaptedTitle=classic_source.title,
        adaptedText=adapted_text,
        cameoInsertionsSummary=cameo_summary_items,
        adaptationNotes=adaptation_notes,
        sceneSeedNotes=scene_seed_notes,
    )


def _request_live_adaptation(
    session: Session,
    classic_source: ClassicSource,
    *,
    adaptation_intensity: str,
) -> ClassicAdaptationStructuredResponse | None:
    if not STORY_GENERATION_API_KEY.strip() or not STORY_GENERATION_MODEL.strip():
        return None

    url = STORY_GENERATION_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {STORY_GENERATION_API_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=STORY_GENERATION_TIMEOUT_SECONDS) as client:
        response = client.post(
            url,
            headers=headers,
            json={
                "model": STORY_GENERATION_MODEL,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": build_classic_adaptation_system_prompt()},
                    {
                        "role": "user",
                        "content": build_classic_adaptation_user_prompt(
                            session,
                            classic_source=classic_source,
                            adaptation_intensity=adaptation_intensity,
                        ),
                    },
                ],
            },
        )
        response.raise_for_status()
        text = _extract_chat_completion_text(response.json())
    if STORY_GENERATION_DEBUG:
        logger.info("Classic adaptation response received for source %s", classic_source.id)
    return parse_classic_adaptation_response_text(text)


def _ensure_scene_seed_notes(
    structured: ClassicAdaptationStructuredResponse,
    *,
    min_scenes: int,
    max_scenes: int,
) -> ClassicAdaptationStructuredResponse:
    if structured.sceneSeedNotes:
        return structured
    return structured.model_copy(
        update={
            "sceneSeedNotes": derive_classic_scene_seed_notes(
                title=structured.adaptedTitle,
                adapted_text=structured.adaptedText,
                min_scenes=min_scenes,
                max_scenes=max_scenes,
            )
        }
    )


def adapt_classic_source(
    session: Session,
    classic_source: ClassicSource,
    *,
    adaptation_intensity: str = "light",
    min_scenes: int = 5,
    max_scenes: int = 6,
) -> ClassicAdaptationResult:
    intensity = validate_classic_adaptation_intensity(adaptation_intensity)
    source = "fallback"
    used_fallback = True
    structured = _fallback_structured_output(
        classic_source,
        adaptation_intensity=intensity,
        min_scenes=min_scenes,
        max_scenes=max_scenes,
    )

    try:
        live_result = _request_live_adaptation(
            session,
            classic_source,
            adaptation_intensity=intensity,
        )
        if live_result is not None:
            live_result = _ensure_scene_seed_notes(live_result, min_scenes=min_scenes, max_scenes=max_scenes)
            validation = validate_classic_adaptation_output(
                source_text=classic_source.source_text,
                adapted=live_result,
            )
            if validation.status != VALIDATION_REJECTED:
                return ClassicAdaptationResult(
                    structured_output=live_result,
                    adaptation_intensity=intensity,
                    validation=validation,
                    source="live_llm",
                    used_fallback=False,
                )
            logger.warning(
                "Classic adaptation live output rejected for source %s; falling back to deterministic mode. Errors: %s",
                classic_source.id,
                validation.errors,
            )
    except Exception:
        logger.exception("Classic adaptation fell back to deterministic mode for source %s", classic_source.id)

    fallback_validation = validate_classic_adaptation_output(
        source_text=classic_source.source_text,
        adapted=structured,
    )
    return ClassicAdaptationResult(
        structured_output=structured,
        adaptation_intensity=intensity,
        validation=fallback_validation,
        source=source,
        used_fallback=used_fallback,
    )
