"""Prompt templates and structured output models for Buddybug Classics.

Example source input (public-domain-compatible mock sample inspired by Goldilocks):

    title = "Goldilocks and the Three Bears"
    source_text = (
        "Once upon a time there were three bears who lived in a little house in the forest. "
        "One morning they left their porridge to cool while they went for a walk. "
        "Soon a little girl named Goldilocks came to the house, tasted the porridge, "
        "tried the chairs, and then fell asleep in the smallest bed. "
        "When the bears returned, they discovered what had happened, and Goldilocks ran away."
    )

Example adaptation configuration:

    adaptation_intensity = "light"

Example structured output shape:

    {
      "adaptedTitle": "Goldilocks and the Three Bears",
      "adaptedText": "...full adapted story...",
      "cameoInsertionsSummary": [
        {
          "insertionLabel": "opening woodland transition",
          "approximateLocation": "near the opening before Goldilocks reaches the house",
          "characters": ["Buddybug"],
          "reason": "Adds a tiny magical witness without changing the plot",
          "plotPreservationNote": "The bears still leave, Goldilocks still arrives alone, and the main events stay unchanged"
        }
      ],
      "adaptationNotes": [
        "Original plot preserved",
        "Buddybug appears briefly near the opening and closing only",
        "No ending changes made"
      ],
      "sceneSeedNotes": [
        {
          "sceneIndex": 1,
          "label": "The bears leave the cottage",
          "excerptAnchor": "the three bears left their porridge to cool",
          "featuredCharacters": ["Father Bear", "Mother Bear", "Baby Bear"],
          "setting": "forest cottage clearing",
          "mood": "peaceful",
          "keyVisualAction": "the bear family walks away from the cottage",
          "illustrationNotes": "Preserve the classic cottage identity; no Buddybug cameo required"
        }
      ]
    }
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models import Character, ClassicSource

CLASSIC_ADAPTATION_INTENSITIES: dict[str, str] = {
    "minimal": (
        "Use almost no additions. Add at most one or two tiny magical cameo touches in the entire story. "
        "Prefer a short descriptive observation over any added dialogue."
    ),
    "light": (
        "Add brief cameo moments in a few natural places only. "
        "Use one to three Buddybug universe presences in total, with very short insertions."
    ),
    "gentle_plus": (
        "Still remain restrained. You may add a few more connective lines than light mode, "
        "but the classic must still dominate clearly and remain recognisably the original story."
    ),
}

DEFAULT_CLASSIC_ADAPTATION_INTENSITY = "light"
CLASSIC_CAMEO_CHARACTER_NAMES = [
    "Buddybug",
    "Verity",
    "Daphne",
    "Dolly",
    "Twinklet",
    "Whisperwing",
    "Glowmoth",
]


class ClassicCameoInsertionSummaryItem(BaseModel):
    insertionLabel: str
    approximateLocation: str
    characters: list[str] = Field(default_factory=list)
    reason: str
    plotPreservationNote: str


class ClassicSceneSeedNote(BaseModel):
    sceneIndex: int
    label: str
    excerptAnchor: str
    featuredCharacters: list[str] = Field(default_factory=list)
    setting: str
    mood: str
    keyVisualAction: str
    illustrationNotes: str


class ClassicAdaptationStructuredResponse(BaseModel):
    adaptedTitle: str
    adaptedText: str
    cameoInsertionsSummary: list[ClassicCameoInsertionSummaryItem] = Field(default_factory=list)
    adaptationNotes: list[str] = Field(default_factory=list)
    sceneSeedNotes: list[ClassicSceneSeedNote] = Field(default_factory=list)


def validate_classic_adaptation_intensity(value: str | None) -> str:
    normalized = (value or DEFAULT_CLASSIC_ADAPTATION_INTENSITY).strip().lower()
    if normalized not in CLASSIC_ADAPTATION_INTENSITIES:
        raise ValueError("Invalid classic adaptation intensity")
    return normalized


def _character_reference_block(session: Session) -> str:
    characters = list(
        session.exec(
            select(Character)
            .where(Character.name.in_(CLASSIC_CAMEO_CHARACTER_NAMES), Character.is_active.is_(True))
            .order_by(Character.name.asc())
        ).all()
    )
    if not characters:
        return "Allowed Buddybug cameo characters: Buddybug, Verity, Daphne, Dolly, Twinklet, Whisperwing, Glowmoth."
    lines = ["Allowed Buddybug cameo characters and canon reminders:"]
    for character in characters:
        lines.append(
            f"- {character.name}: {character.short_description} "
            f"Personality: {character.personality_traits}. Visual canon: {character.visual_description}"
        )
    return "\n".join(lines)


def build_classic_adaptation_system_prompt() -> str:
    return "\n".join(
        [
            "Role:",
            "You are a strict editorial adaptation assistant for Buddybug Classics.",
            "",
            "Task:",
            "Adapt a public-domain classic story into a Buddybug-enhanced version that remains clearly and recognisably the original classic.",
            "",
            "Non-negotiable constraints:",
            "- Preserve the original story as closely as possible.",
            "- Preserve the same core events in the same order.",
            "- Preserve the same protagonist, central conflict, message, and ending.",
            "- Keep the final story clearly recognisable as the original classic tale.",
            "- Add less rather than more.",
            "- When in doubt, preserve the original sentence or scene.",
            "- Do not improve the story by rewriting it; preserve it.",
            "",
            "Allowed additions:",
            "- Sparse Buddybug cameo presences only.",
            "- Brief magical observations.",
            "- Short scene-transition lines.",
            "- Gentle witness or guide moments that do not alter the plot.",
            "",
            "Forbidden changes:",
            "- Do not change the ending.",
            "- Do not change the identity of the protagonist.",
            "- Do not change the moral or central message.",
            "- Do not introduce large new subplots.",
            "- Do not replace original characters with Buddybug characters.",
            "- Do not make Buddybug or friends the main character.",
            "- Do not let Buddybug characters solve the central conflict.",
            "- Do not replace iconic original scenes.",
            "- Do not add long new dialogue exchanges.",
            "- Do not modernize the setting unless source normalization absolutely requires it.",
            "- Do not turn the story into parody, satire, comedy rewrite, or a modern retelling.",
            "- Do not insert branding language inside the story body.",
            "- Do not output commentary, headings, or instructions in the story text.",
            "",
            "Editorial method:",
            "1. Read the original story carefully.",
            "2. Identify the essential story beats.",
            "3. Preserve every essential beat in order.",
            "4. Identify 2 to 5 natural insertion points for subtle Buddybug cameo moments.",
            "5. Insert only brief lines or tiny phrases where suitable.",
            "6. Re-read for coherence.",
            "7. Ensure the result still reads as the original classic.",
            "",
            "Output format:",
            "- Return a single JSON object only.",
            "- Do not wrap the JSON in markdown fences.",
            "- Use the required keys exactly as requested.",
        ]
    )


def build_classic_adaptation_user_prompt(
    session: Session,
    *,
    classic_source: ClassicSource,
    adaptation_intensity: str,
) -> str:
    intensity = validate_classic_adaptation_intensity(adaptation_intensity)
    return "\n".join(
        [
            "Classic adaptation request:",
            f"Title: {classic_source.title}",
            f"Source author: {classic_source.source_author or 'Unknown / public-domain source'}",
            f"Source reference: {classic_source.source_url}",
            f"Adaptation intensity: {intensity}",
            f"Intensity rule: {CLASSIC_ADAPTATION_INTENSITIES[intensity]}",
            "",
            _character_reference_block(session),
            "",
            "Character usage rules:",
            "- Usually only 1 to 3 Buddybug cameo presences should appear in a single adapted classic.",
            "- Buddybug is the most natural cameo option.",
            "- Verity should be used sparingly unless naturally appropriate.",
            "- Not all characters need to appear.",
            "- Cameo appearances must be brief.",
            "- Buddybug characters must not dominate dialogue or decision-making.",
            "",
            "Required output JSON shape:",
            "{",
            '  "adaptedTitle": "string",',
            '  "adaptedText": "string",',
            '  "cameoInsertionsSummary": [',
            "    {",
            '      "insertionLabel": "string",',
            '      "approximateLocation": "string",',
            '      "characters": ["string"],',
            '      "reason": "string",',
            '      "plotPreservationNote": "string"',
            "    }",
            "  ],",
            '  "adaptationNotes": ["string"],',
            '  "sceneSeedNotes": [',
            "    {",
            '      "sceneIndex": 1,',
            '      "label": "string",',
            '      "excerptAnchor": "string",',
            '      "featuredCharacters": ["string"],',
            '      "setting": "string",',
            '      "mood": "string",',
            '      "keyVisualAction": "string",',
            '      "illustrationNotes": "string"',
            "    }",
            "  ]",
            "}",
            "",
            "Scene seed note rules:",
            "- Preserve iconic scenes from the classic.",
            "- Include Buddybug characters in a scene only if they are truly present in that part of the story.",
            "- Do not force cameos into every scene.",
            "- Keep scene notes useful for later illustration planning.",
            "",
            "Original source text follows:",
            classic_source.source_text.strip(),
        ]
    )


def build_classic_scene_breakdown_prompt(
    *,
    title: str,
    adapted_text: str,
    adaptation_intensity: str,
) -> str:
    intensity = validate_classic_adaptation_intensity(adaptation_intensity)
    return "\n".join(
        [
            "Role:",
            "You create scene seed notes for Buddybug Classics illustration planning.",
            "",
            "Task:",
            "Turn the adapted classic below into visually meaningful scene notes without changing the story.",
            "",
            "Rules:",
            "- Preserve iconic scenes from the classic.",
            "- Reflect the adapted classic faithfully.",
            "- Include Buddybug characters only when they are truly present in that part of the story.",
            "- Do not force cameos into every page.",
            f"- Respect the adaptation intensity already used: {intensity}.",
            "",
            "Return JSON only using the sceneSeedNotes array shape already defined.",
            "",
            f"Title: {title}",
            "Adapted story text:",
            adapted_text.strip(),
        ]
    )


def build_classic_illustration_enhancer(
    *,
    scene_note: ClassicSceneSeedNote | None,
    adaptation_intensity: str,
) -> str:
    intensity = validate_classic_adaptation_intensity(adaptation_intensity)
    lines = [
        "Classic story illustration mode:",
        "- Preserve the original classic scene identity and atmosphere.",
        "- Keep the Buddybug house art style, but do not clutter the page with unnecessary extra characters.",
        "- If a Buddybug cameo is not actually present in this scene, do not add one visually.",
        "- Maintain bedtime warmth, storybook composition, and child-friendly clarity.",
        "- Preserve fairytale or classic-story cues where they are relevant to the scene.",
        f"- Adaptation intensity for visual cameo restraint: {intensity}.",
    ]
    if scene_note is not None:
        lines.extend(
            [
                f"- Scene seed label: {scene_note.label}.",
                f"- Excerpt anchor: {scene_note.excerptAnchor}.",
                f"- Key visual action: {scene_note.keyVisualAction}.",
                f"- Illustration note: {scene_note.illustrationNotes}.",
            ]
        )
    return "\n".join(lines)


def _classic_context_excerpt(page_text: str | None) -> str | None:
    if not page_text:
        return None
    cleaned = re.sub(r"\s+", " ", page_text).strip()
    if not cleaned:
        return None
    return cleaned[:180].rstrip() + ("..." if len(cleaned) > 180 else "")


def build_classic_illustration_prompt(
    *,
    page_number: int,
    page_text: str,
    scene_summary: str,
    setting: str,
    mood: str,
    key_visual_action: str,
    characters_present: list[str],
    adaptation_intensity: str,
    scene_note: ClassicSceneSeedNote | None = None,
    previous_page_text: str | None = None,
    next_page_text: str | None = None,
) -> str:
    intensity = validate_classic_adaptation_intensity(adaptation_intensity)
    clean_setting = re.sub(r"\s+", " ", setting).strip() or "the exact classic story setting from the page text"
    clean_mood = re.sub(r"\s+", " ", mood).strip() or "storybook calm"
    clean_action = re.sub(r"\s+", " ", key_visual_action).strip() or "the clearest iconic action from this page"
    characters_text = ", ".join(characters_present) if characters_present else "original classic story characters only"

    lines = [
        "Create one children's storybook illustration for a single Buddybug Classics page.",
        "Pick one main visual moment only. Do not try to show the whole story at once.",
        f"Page number: {page_number}",
        f"Exact text: {page_text.strip()}",
        f"Scene summary: {scene_summary.strip()}",
        f"Classic setting: {clean_setting}.",
        f"This image must be clearly and unmistakably set in {clean_setting}.",
        f"Characters present in this exact scene: {characters_text}.",
        f"Key visual action to show: {clean_action}.",
        f"Emotional tone: {clean_mood}.",
        "Style: high-end Pixar-style animated storybook illustration, rounded friendly shapes, premium film-quality finish, child-friendly clarity, suitable for ages 3-7.",
        "Classic illustration rules:",
        "- Preserve the original classic scene identity and atmosphere.",
        "- Keep the Buddybug house art style, but make the actual story setting and action the priority.",
        "- Include Buddybug cameo characters only if they are truly present in this page text.",
        "- If no Buddybug cameo is present in this scene, do not add one visually.",
        "- Preserve fairytale and period-appropriate classic-story cues where relevant.",
        f"- Adaptation intensity for visual cameo restraint: {intensity}.",
        "Hard setting guardrails:",
        "- Do not substitute a generic Buddybug bedtime setting.",
        "- Do not substitute default magical garden details or generic glowing paths unless this exact page text truly requires them.",
        "- Do not convert indoor classic scenes into a nursery, bedtime bedroom, or generic cozy room unless the source scene is actually a bedroom.",
        "- If the source scene is a bedroom, keep it as the classic story's own bedroom, not a default Buddybug room.",
        "- Keep props, architecture, clothing, and surroundings faithful to this classic scene.",
        "Negative prompt: do not relocate the scene; do not use a generic bedtime room; do not use a generic magical garden; no text, captions, labels, watermarks, or readable writing inside the artwork.",
    ]
    if scene_note is not None:
        lines.extend(
            [
                f"Scene seed label: {scene_note.label}.",
                f"Excerpt anchor: {scene_note.excerptAnchor}.",
                f"Scene note setting: {scene_note.setting}.",
                f"Scene note illustration guidance: {scene_note.illustrationNotes}.",
            ]
        )
    previous_excerpt = _classic_context_excerpt(previous_page_text)
    if previous_excerpt:
        lines.append(f"Previous page context: {previous_excerpt}")
    next_excerpt = _classic_context_excerpt(next_page_text)
    if next_excerpt:
        lines.append(f"Next page context: {next_excerpt}")
    return "\n".join(lines)


def parse_classic_adaptation_response_text(raw_text: str) -> ClassicAdaptationStructuredResponse:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return ClassicAdaptationStructuredResponse.model_validate_json(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return ClassicAdaptationStructuredResponse.model_validate(json.loads(match.group(0)))


def render_cameo_insertions_summary(items: list[ClassicCameoInsertionSummaryItem]) -> str:
    if not items:
        return "- No cameo insertions were recorded."
    lines: list[str] = []
    for item in items:
        characters = ", ".join(item.characters) if item.characters else "No Buddybug cameo characters listed"
        lines.append(
            f"- {item.insertionLabel}: {characters}. Location: {item.approximateLocation}. "
            f"Reason: {item.reason}. Plot preserved: {item.plotPreservationNote}."
        )
    return "\n".join(lines)


def render_adaptation_notes(notes: list[str]) -> str:
    cleaned = [note.strip() for note in notes if note and note.strip()]
    if not cleaned:
        return "Original plot preserved."
    return "\n".join(f"- {note}" for note in cleaned)


def render_scene_seed_notes_json(notes: list[ClassicSceneSeedNote]) -> str:
    return json.dumps([note.model_dump() for note in notes], indent=2)
