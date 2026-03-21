from __future__ import annotations

import re

from app.schemas.story_pipeline_schema import StoryMetadata, StoryOutline

POETIC_FILLER_PATTERNS = [
    r"\bmoonlight\b",
    r"\bglowing stars\b",
    r"\bwhispering breeze\b",
    r"\bsilver light\b",
    r"\bdreamy\b",
    r"\bsoft silver\b",
    r"\bwhat kindness smells like\b",
]

ATMOSPHERIC_OPENER_PATTERNS = [
    r"^under the",
    r"^in the soft",
    r"^beneath the",
    r"^the moonlight",
    r"^the breeze",
]


def _paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]


def _clean_poetic_filler(text: str) -> str:
    cleaned = text
    for pattern in POETIC_FILLER_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;!?])", r"\1", cleaned)
    return cleaned.strip()


def _simplify_long_sentences(paragraph: str) -> str:
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", paragraph) if item.strip()]
    rewritten: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= 28:
            rewritten.append(sentence)
            continue
        midpoint = max(8, len(words) // 2)
        split_index = None
        preferred_breaks = {
            "but",
            "so",
            "when",
        }
        search_start = max(7, midpoint - 5)
        search_end = min(len(words) - 4, midpoint + 5)
        for idx in range(search_end, search_start - 1, -1):
            token = words[idx].rstrip(",;:").casefold()
            if token in preferred_breaks:
                split_index = idx
                break
        if split_index is None:
            rewritten.append(sentence)
            continue

        left = " ".join(words[:split_index]).rstrip(",")
        right = " ".join(words[split_index:])
        if len(left.split()) < 6 or len(right.split()) < 6:
            rewritten.append(sentence)
            continue
        if not left.endswith((".", "!", "?")):
            left += "."
        rewritten.append(left)
        rewritten.append(right[:1].upper() + right[1:] if right else "")
    return " ".join(item for item in rewritten if item).strip()


def _opening_needs_tightening(first_paragraph: str) -> bool:
    lowered = first_paragraph.casefold()
    return any(re.search(pattern, lowered) for pattern in ATMOSPHERIC_OPENER_PATTERNS)


def rewrite_story_to_buddybug_style(
    *,
    generated_story: str,
    outline: StoryOutline,
    metadata: StoryMetadata,
) -> str:
    """Rewrite a generated story into the tighter Buddybug house style."""
    paragraphs = _paragraphs(_clean_poetic_filler(generated_story))
    if len(paragraphs) < 4:
        paragraphs = [
            outline.opening_hook,
            outline.problem,
            outline.event,
            outline.resolution,
            outline.gentle_ending,
        ]
    if not paragraphs:
        paragraphs = [outline.opening_hook, outline.problem, outline.event, outline.resolution, outline.gentle_ending]

    if _opening_needs_tightening(paragraphs[0]):
        lead = metadata.main_characters[0] if metadata.main_characters else "Buddybug"
        opener = f"{outline.opening_hook} \"I can sort it out,\" said {lead}."
        if len(paragraphs) == 1:
            paragraphs = [opener]
        else:
            paragraphs[0] = opener

    paragraphs = [_simplify_long_sentences(paragraph) for paragraph in paragraphs]

    if '"' not in "\n\n".join(paragraphs):
        speaker = metadata.main_characters[1] if len(metadata.main_characters) > 1 else metadata.main_characters[0]
        if len(paragraphs) > 1:
            paragraphs[1] = f"{paragraphs[1]} \"We can do this one step at a time,\" said {speaker}."
        else:
            paragraphs.append(f"\"We can do this one step at a time,\" said {speaker}.")

    if metadata.mode == "bedtime" and len(paragraphs) >= 1:
        if "quiet" not in paragraphs[-1].casefold() and "comfort" not in paragraphs[-1].casefold():
            paragraphs[-1] = f"{paragraphs[-1]} The room felt quiet and comforting again."
    if metadata.mode != "bedtime" and len(paragraphs) >= 3:
        middle = paragraphs[2]
        if "giggle" not in middle.casefold() and "laugh" not in middle.casefold():
            paragraphs[2] = f"{middle} That was the moment the first real giggle slipped out."

    if len(paragraphs) >= 2 and outline.resolution.casefold() not in paragraphs[-2].casefold():
        paragraphs[-2] = f"{paragraphs[-2]} {outline.resolution}"
    if paragraphs and outline.gentle_ending.casefold() not in paragraphs[-1].casefold():
        paragraphs[-1] = f"{paragraphs[-1]} {outline.gentle_ending}"

    rewritten = "\n\n".join(paragraphs).strip()
    rewritten = re.sub(r"[ \t]{2,}", " ", rewritten)
    return rewritten
