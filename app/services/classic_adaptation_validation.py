from __future__ import annotations

from dataclasses import dataclass
import re

from app.services.classic_prompt_templates import (
    CLASSIC_CAMEO_CHARACTER_NAMES,
    ClassicAdaptationStructuredResponse,
)

VALIDATION_ACCEPTED = "accepted"
VALIDATION_ACCEPTED_WITH_WARNINGS = "accepted_with_warnings"
VALIDATION_REJECTED = "rejected"

META_RESPONSE_PATTERNS = [
    r"here is your adapted version",
    r"here is the adapted version",
    r"adapted version:",
    r"json",
    r"output:",
    r"scene seed notes",
    r"cameo insertions summary",
    r"adaptation notes",
]


@dataclass(frozen=True)
class ClassicAdaptationValidationResult:
    status: str
    warnings: list[str]
    errors: list[str]
    paragraph_count_original: int
    paragraph_count_adapted: int
    length_ratio: float
    unique_cameo_character_count: int


def _paragraph_count(text: str) -> int:
    parts = [part.strip() for part in re.split(r"\n\s*\n", text or "") if part.strip()]
    return len(parts) if parts else (1 if (text or "").strip() else 0)


def _normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _significant_words(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z']+", (text or "").casefold())
    return {token for token in tokens if len(token) >= 4}


def _unique_cameo_characters_in_text(text: str) -> list[str]:
    lowered = (text or "").casefold()
    return [name for name in CLASSIC_CAMEO_CHARACTER_NAMES if name.casefold() in lowered]


def validate_classic_adaptation_output(
    *,
    source_text: str,
    adapted: ClassicAdaptationStructuredResponse,
) -> ClassicAdaptationValidationResult:
    warnings: list[str] = []
    errors: list[str] = []

    original_text = _normalized_text(source_text)
    adapted_text = _normalized_text(adapted.adaptedText)
    title = _normalized_text(adapted.adaptedTitle)

    if not title:
        errors.append("Adapted title is empty.")
    if not adapted_text:
        errors.append("Adapted text is empty.")
    if not adapted.cameoInsertionsSummary:
        errors.append("No cameo insertion summary items were returned.")

    paragraph_count_original = _paragraph_count(source_text)
    paragraph_count_adapted = _paragraph_count(adapted.adaptedText)
    original_word_count = max(len(original_text.split()), 1)
    adapted_word_count = len(adapted_text.split())
    length_ratio = adapted_word_count / original_word_count if original_word_count else 0.0

    if length_ratio > 1.45:
        errors.append("Adapted text is dramatically longer than the original source.")
    elif length_ratio > 1.2:
        warnings.append("Adapted text is noticeably longer than the original source.")
    if length_ratio < 0.55:
        errors.append("Adapted text is dramatically shorter than the original source.")
    elif length_ratio < 0.75:
        warnings.append("Adapted text is noticeably shorter than the original source.")

    paragraph_delta = abs(paragraph_count_adapted - paragraph_count_original)
    if paragraph_delta >= max(3, int(max(paragraph_count_original, 1) * 0.6)):
        errors.append("Adapted paragraph structure differs too much from the original source.")
    elif paragraph_delta >= 2:
        warnings.append("Adapted paragraph structure differs from the original source.")

    present_cameo_characters = _unique_cameo_characters_in_text(adapted.adaptedText)
    if len(present_cameo_characters) > 4:
        errors.append("Too many Buddybug characters appear in the adapted text.")
    elif len(present_cameo_characters) > 3:
        warnings.append("More Buddybug characters appear than the preferred restrained limit.")

    adapted_lower = adapted.adaptedText.casefold()
    for pattern in META_RESPONSE_PATTERNS:
        if re.search(pattern, adapted_lower):
            errors.append(f"Adapted text contains meta-response pattern: {pattern}.")
            break

    if re.search(r"^\s*(title|heading|summary)\s*:", adapted.adaptedText, flags=re.IGNORECASE | re.MULTILINE):
        errors.append("Adapted text contains heading-style output instead of story body only.")

    if any(len(item.characters) > 3 for item in adapted.cameoInsertionsSummary):
        warnings.append("At least one cameo summary item includes too many Buddybug characters.")
    if not any("preserv" in item.plotPreservationNote.casefold() for item in adapted.cameoInsertionsSummary):
        warnings.append("Cameo summary does not explicitly confirm plot preservation.")

    source_paragraphs = [part.strip() for part in re.split(r"\n\s*\n", source_text) if part.strip()]
    adapted_paragraphs = [part.strip() for part in re.split(r"\n\s*\n", adapted.adaptedText) if part.strip()]
    if source_paragraphs and adapted_paragraphs:
        source_ending_words = _significant_words(source_paragraphs[-1])
        adapted_ending_words = _significant_words(adapted_paragraphs[-1])
        if source_ending_words:
            overlap = len(source_ending_words & adapted_ending_words) / len(source_ending_words)
            if overlap < 0.15:
                warnings.append("Adapted ending appears materially different from the source ending and should be reviewed.")

    if errors:
        status = VALIDATION_REJECTED
    elif warnings:
        status = VALIDATION_ACCEPTED_WITH_WARNINGS
    else:
        status = VALIDATION_ACCEPTED

    return ClassicAdaptationValidationResult(
        status=status,
        warnings=warnings,
        errors=errors,
        paragraph_count_original=paragraph_count_original,
        paragraph_count_adapted=paragraph_count_adapted,
        length_ratio=round(length_ratio, 3),
        unique_cameo_character_count=len(present_cameo_characters),
    )
