import re
from dataclasses import dataclass

from app.models import StoryDraft, StoryIdea
from app.schemas.story_pipeline_schema import IllustrationScene
from app.services.illustration_canon import build_character_visual_lines, build_location_visual_lines, get_location_visual_canon
from app.services.story_planner import build_illustration_scenes, build_story_outline

CANONICAL_CHARACTERS = [
    "Verity",
    "Dolly",
    "Daphne",
    "Buddybug",
    "Glowmoth",
    "Twinklet",
    "Whisperwing",
]

IMAGE_STATUSES = {
    "not_started",
    "prompt_ready",
    "image_generated",
    "image_approved",
    "image_rejected",
}

STYLE_SUFFIX = (
    "high-end Pixar-style animated storybook illustration, warm cinematic bedtime lighting, rounded friendly shapes, "
    "clear story action, expressive but not exaggerated faces, premium film-quality finish, suitable for ages 3-7"
)

LOCATION_KEYWORDS = {
    "zoo picnic lawn": ["zoo", "picnic", "basket", "checked cloth", "picnic grass", "footprints", "elephant", "rail"],
    "family kitchen": ["kitchen", "mix", "mixing bowl", "bowl", "flour", "oven", "bake", "baking", "muffin", "bread", "blueberries", "wooden spoon", "table"],
    "family living room": ["living room", "sitting room", "sofa", "couch", "armchair", "coffee table", "hearth", "fireplace", "blanket fort", "pillow fort", "fort", "forts", "den"],
    "library reading nook": ["library reading nook", "library", "bookshelf", "book basket", "cushions", "soft rug", "stacked books"],
    "moonlit garden": ["moonlit garden", "moonlight", "glowing path", "lantern", "lanterns", "petals", "soft shrubs"],
    "cozy bedroom": ["bed", "blanket", "pillows", "bedroom", "room", "lantern", "nightgown"],
    "breakfast kitchen": ["kitchen", "mix", "mixing bowl", "bowl", "flour", "oven", "bake", "baking", "muffin", "bread", "blueberries", "wooden spoon", "table"],
    "quiet forest": ["forest", "trees", "leaves", "branch", "path through the woods"],
    "storybook clearing": ["clearing", "storybook", "open glade"],
    "sleepy meadow": ["meadow", "tall grass", "field"],
    "nighttime path": ["path", "pathway", "trail", "walk"],
    "by the window": ["window", "windowsill"],
    "inside the house": ["house", "hall", "doorway", "hearth"],
    "reading nook": ["reading nook", "bookshelf", "stacked books", "cushions", "soft rug", "book basket"],
}

MOOD_KEYWORDS = {
    "sleepy": ["sleep", "sleepy", "pillows", "bedtime", "lullaby", "dream"],
    "comforting": ["warm", "cozy", "comfort", "steady", "kind", "gentle hearts"],
    "magical": ["glow", "sparkle", "moonlight", "shimmer", "magic", "storylight"],
    "gently curious": ["wonder", "noticed", "curious", "looked", "watched"],
    "reassured": ["safe", "steady", "reassured", "all was well"],
    "dreamy": ["drifted", "moonlight", "whisper", "soft", "dreamy"],
    "calm": ["calm", "quiet", "slow", "breath", "still"],
    "peaceful": ["peaceful", "hush", "rest", "peace", "softly"],
}

OBJECT_KEYWORDS = {
    "storybook": ["book", "storybook", "pages"],
    "blanket": ["blanket", "quilt", "coverlet"],
    "fort": ["fort", "forts", "blanket fort", "pillow fort", "homemade fort", "homemade forts", "den"],
    "sofa": ["sofa", "couch", "armchair"],
    "chair": ["chair", "chairs", "dining chair"],
    "sheet": ["sheet", "sheets"],
    "basket": ["basket", "woven basket", "basket bed"],
    "mixing bowl": ["mixing bowl", "bowl of batter", "bowl"],
    "wooden spoon": ["wooden spoon", "spoon"],
    "blueberries": ["blueberries", "berry", "berries"],
    "flour": ["flour", "flour dust", "batter"],
    "oven": ["oven", "baking tray", "tray of muffins", "muffins", "bread"],
    "pond": ["pond", "ripples", "lily pads", "water"],
    "flowers": ["flowers", "petals", "daisies", "garden"],
    "window": ["window", "curtains", "glass"],
    "lamp": ["lamp", "lantern", "bedside light"],
    "moon": ["moon", "crescent moon", "stars"],
    "tree": ["tree", "apple tree", "story tree"],
    "path": ["path", "trail", "glowing path"],
}

LOCATION_REQUIRED_PROPS = {
    "zoo picnic lawn": ("picnic basket", "checked picnic cloth", "open grass", "zoo rail or animal-area cue"),
    "family kitchen": ("mixing bowl", "wooden spoon", "kitchen table or worktop", "baking ingredients"),
    "family living room": ("sofa or armchair", "blanket fort or cushion fort structure", "rug or coffee table", "indoor family room details"),
    "breakfast kitchen": ("mixing bowl", "wooden spoon", "kitchen table or worktop", "baking ingredients"),
    "library reading nook": ("stacked books", "soft rug", "cushions", "low shelf or book basket"),
    "cozy bedroom": ("bed", "pillows", "blanket", "bedside or bedroom furniture"),
    "reading nook": ("stacked books", "soft rug", "cushions", "low shelf or book basket"),
    "moonlit garden": ("flowers", "garden greenery", "path or open grass"),
    "garden path": ("path stones", "flowers", "garden leaves"),
}

LOCATION_NEGATIVE_ELEMENTS = {
    "zoo picnic lawn": (
        "do not turn the scene into a moonlit garden",
        "do not add glowing garden paths or bedtime lantern trails unless the text clearly asks for them",
        "do not replace the picnic lawn with a bedroom or generic magical garden",
    ),
    "family kitchen": (
        "do not place the scene outdoors in a garden",
        "do not add glowing garden paths, lantern trails, or flower beds as the main setting",
        "do not place the scene on a bed",
        "do not show bedroom pillows or blankets as the main setting",
        "do not use a nursery or bedtime bedroom composition",
        "do not replace the kitchen with a generic cozy room",
    ),
    "family living room": (
        "do not turn the scene into a bedroom",
        "do not use a bed as the main set piece unless the page text clearly says so",
        "do not replace the fort with bedtime pillows by a bed",
        "do not move the scene outdoors into a moonlit garden",
    ),
    "breakfast kitchen": (
        "do not place the scene on a bed",
        "do not show bedroom pillows or blankets as the main setting",
        "do not use a nursery or bedtime bedroom composition",
        "do not replace the kitchen with a generic cozy room",
    ),
    "cozy bedroom": (
        "do not turn the scene into a kitchen",
        "do not use kitchen counters or baking setup unless the text clearly requires it",
    ),
    "reading nook": (
        "do not place the scene on a bed unless the text clearly says so",
        "do not replace the nook with a kitchen or dining room",
    ),
    "library reading nook": (
        "do not place the scene on a bed unless the text clearly says so",
        "do not replace the library nook with a kitchen, garden, or dining room",
    ),
    "moonlit garden": (
        "do not use this location unless the page text clearly supports a moonlit outdoor garden scene",
        "do not add beds, kitchen worktops, or indoor reading nooks as the main setting",
    ),
}

VISUAL_ACTION_TERMS = {
    "looked",
    "look",
    "watched",
    "noticed",
    "found",
    "held",
    "sat",
    "settled",
    "moved",
    "walked",
    "listened",
    "tucked",
    "smiled",
    "glowed",
    "shimmered",
    "hovered",
    "opened",
    "read",
    "rested",
}

ABSTRACT_ACTION_TERMS = {
    "kindness",
    "courage",
    "understanding",
    "feeling",
    "feelings",
    "truth",
    "magic",
    "bedtime",
    "lesson",
    "peaceful",
}

GENERIC_BEAT_ACTION_FRAGMENTS = {
    "not quite right",
    "sort it out",
    "the central problem",
    "the clearest story action",
    "the problem being solved",
    "warm settled ending",
    "fix the problem",
    "one step at a time",
    "spotted the clue",
    "felt much smaller",
}

VISUAL_REWRITE_CUES = {
    "noticed",
    "listened",
    "watched",
    "looked",
    "smile",
    "glow",
    "shimmer",
    "breeze",
    "breath",
    "reassured",
    "restful",
    "settled",
    "wondered",
    "safe",
}

ABSTRACT_ACTION_PREFIXES = {
    "they listened to",
    "with everything back in place",
    "with daphne, they noticed",
    "verity and dolly felt reassured",
    "let us notice",
    "that was when",
    "soon a tiny worry",
}


@dataclass(frozen=True)
class IllustrationPageBrief:
    page_number: int
    exact_text: str
    scene_location: str
    characters_present: list[str]
    key_action: str
    emotional_tone: str
    important_objects: list[str]
    time_of_day_lighting: str
    composition_note: str
    continuity_notes: list[str]


def _source_text(story_draft: StoryDraft) -> str:
    return (story_draft.approved_text or story_draft.full_text).strip()


def _split_sentences(paragraph: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", paragraph.strip()) if item.strip()]


def _prepare_units(source_text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", source_text) if part.strip()]
    units: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph.split()) <= 90:
            units.append(paragraph)
            continue

        sentences = _split_sentences(paragraph)
        current: list[str] = []
        current_words = 0
        for sentence in sentences:
            sentence_words = len(sentence.split())
            if current and current_words + sentence_words > 70:
                units.append(" ".join(current).strip())
                current = [sentence]
                current_words = sentence_words
            else:
                current.append(sentence)
                current_words += sentence_words
        if current:
            units.append(" ".join(current).strip())

    return units


def _choose_target_page_count(
    word_count: int,
    target_page_count: int | None,
    min_pages: int,
    max_pages: int,
) -> int:
    min_pages, max_pages = sorted((min_pages, max_pages))
    if target_page_count is not None:
        return max(min_pages, min(max_pages, target_page_count))

    heuristic = round(word_count / 85)
    return max(min_pages, min(max_pages, heuristic))


def _chunk_units(units: list[str], target_page_count: int) -> list[str]:
    if not units:
        return []

    total_words = sum(len(unit.split()) for unit in units)
    target_words = max(45, round(total_words / max(target_page_count, 1)))

    pages: list[str] = []
    current_units: list[str] = []
    current_words = 0

    for index, unit in enumerate(units):
        unit_words = len(unit.split())
        remaining_units = len(units) - index
        remaining_pages = max(target_page_count - len(pages), 1)

        should_flush = (
            current_units
            and current_words >= target_words
            and remaining_units >= remaining_pages
        )
        if should_flush:
            pages.append("\n\n".join(current_units).strip())
            current_units = []
            current_words = 0

        current_units.append(unit)
        current_words += unit_words

    if current_units:
        pages.append("\n\n".join(current_units).strip())

    while len(pages) < target_page_count and any(len(page.split()) > 90 for page in pages):
        longest_index = max(range(len(pages)), key=lambda idx: len(pages[idx].split()))
        longest_page = pages.pop(longest_index)
        sentences = _split_sentences(longest_page)
        split_at = max(1, len(sentences) // 2)
        first_half = " ".join(sentences[:split_at]).strip()
        second_half = " ".join(sentences[split_at:]).strip()
        replacement = [part for part in [first_half, second_half] if part]
        pages[longest_index:longest_index] = replacement

    return pages[:target_page_count] if len(pages) > target_page_count else pages


def _infer_location(page_text: str, fallback: str) -> str:
    lowered = page_text.casefold()
    best_location = fallback
    best_score = 0
    for location, keywords in LOCATION_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_location = location
            best_score = score
    return best_location


def _infer_mood(page_text: str) -> str:
    lowered = page_text.casefold()
    best_mood = "peaceful"
    best_score = 0
    for mood, keywords in MOOD_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_mood = mood
            best_score = score
    return best_mood


def _detect_characters(page_text: str) -> list[str]:
    lowered = page_text.casefold()
    return [name for name in CANONICAL_CHARACTERS if name.casefold() in lowered]


def _scene_summary(page_text: str, location: str, mood: str, beat: IllustrationScene | None = None) -> str:
    sentences = _split_sentences(page_text)
    first_sentence = sentences[0] if sentences else page_text.strip()
    text_summary = first_sentence.rstrip(".")
    if beat is not None:
        return f"{beat.label} in {location} with a {mood} feeling: {beat.text} {text_summary}."
    return f"Story scene in {location} with a {mood} feeling: {text_summary}."


def _context_excerpt(page_text: str | None) -> str | None:
    if not page_text:
        return None
    sentences = _split_sentences(page_text)
    if not sentences:
        return None
    excerpt = sentences[0].strip()
    if len(excerpt) > 180:
        excerpt = f"{excerpt[:177].rstrip()}..."
    return excerpt


def _dedupe_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return ordered


def _style_suffix_for_story(story_idea: StoryIdea | None) -> str:
    if story_idea is None:
        return STYLE_SUFFIX
    normalized_tone = (story_idea.tone or "").casefold()
    if any(token in normalized_tone for token in ["playful", "cheeky", "mischief", "fun"]):
        return (
            "high-end Pixar-style animated storybook illustration, playful but tidy action, warm daylight or cozy indoor lighting, "
            "friendly faces, gentle humour, premium film-quality finish, suitable for ages 3-7"
        )
    if story_idea.age_band == "8-12":
        return (
            "high-end animated storybook illustration, clear scene action, thoughtful mystery energy, child-friendly detail, "
            "cinematic but emotionally safe and suitable for ages 8-12"
        )
    return STYLE_SUFFIX


def _clean_sentence(sentence: str) -> str:
    cleaned = sentence.strip().strip('"').strip("'")
    return re.sub(r"\s+", " ", cleaned).strip()


def _best_visual_sentence(page_text: str) -> str | None:
    sentences = _split_sentences(page_text)
    if not sentences:
        return None
    best_sentence: str | None = None
    best_score = -1
    for sentence in sentences:
        cleaned = _clean_sentence(sentence)
        lowered = cleaned.casefold()
        score = 0
        if any(name.casefold() in lowered for name in CANONICAL_CHARACTERS):
            score += 3
        score += sum(2 for token in VISUAL_ACTION_TERMS if re.search(rf"\b{re.escape(token)}\b", lowered))
        score += sum(1 for keywords in OBJECT_KEYWORDS.values() if any(keyword in lowered for keyword in keywords))
        score -= sum(1 for token in ABSTRACT_ACTION_TERMS if re.search(rf"\b{re.escape(token)}\b", lowered))
        if cleaned.startswith(("Let us", "That was when", "Soon a tiny worry")):
            score -= 2
        if score > best_score:
            best_sentence = cleaned
            best_score = score
    return best_sentence


def _is_generic_beat_action(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in GENERIC_BEAT_ACTION_FRAGMENTS)


def _lead_character_name(characters: list[str]) -> str:
    if "Verity" in characters:
        return "Verity"
    return characters[0] if characters else "the main character"


def _other_character_names(characters: list[str], *, lead_name: str) -> list[str]:
    return [name for name in characters if name != lead_name]


def _join_names(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def _lead_plus_others_text(lead_name: str, others: list[str]) -> str:
    if not others:
        return lead_name
    return _join_names([lead_name, *others])


def _location_props(location: str) -> list[str]:
    canon = get_location_visual_canon(location)
    if canon is None:
        return []
    return list(canon.recurring_props)


def _location_required_props(location: str) -> list[str]:
    canon = get_location_visual_canon(location)
    configured = LOCATION_REQUIRED_PROPS.get((location or "").strip().casefold(), ())
    props = list(configured)
    if canon is not None:
        for prop in canon.recurring_props:
            if prop not in props:
                props.append(prop)
    return props


def _location_negative_elements(location: str) -> list[str]:
    return list(LOCATION_NEGATIVE_ELEMENTS.get((location or "").strip().casefold(), ()))


def _first_matching_object(page_text: str) -> str | None:
    lowered = page_text.casefold()
    for label, keywords in OBJECT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return label
    return None


def _select_visual_role(*, page_number: int, page_count: int, page_text: str, mood: str, location: str) -> str:
    lowered = page_text.casefold()
    lowered_location = location.casefold()
    if "living room" in lowered_location:
        if any(token in lowered for token in {"fort", "forts", "blanket fort", "pillow fort", "den", "sheet", "sofa", "couch"}):
            return "gentle_pause"
    if any(token in lowered_location for token in {"kitchen", "reading nook"}):
        if any(token in lowered for token in {"mix", "bake", "bowl", "flour", "oven", "spoon", "books", "shelf", "stack"}):
            return "gentle_pause"
    if page_number == 1:
        return "opening_tableau"
    if page_number == page_count:
        return "sleepy_settle"
    if any(token in lowered for token in {"blanket", "pillow", "pillows", "tucked", "cushion", "sleep"}):
        if any(token in lowered for token in {"fort", "forts", "blanket fort", "pillow fort", "den"}) or "living room" in lowered_location:
            return "gentle_pause"
        return "sleepy_settle"
    if any(token in lowered for token in {"kindness", "reassured", "shared glance", "kind word", "gentle hearts", "shine"}):
        return "reassuring_connection"
    if any(token in lowered for token in {"listen", "hush", "breeze", "quiet", "silence"}):
        return "listening_pause"
    if any(token in lowered for token in {"glow", "shimmer", "moonlight", "reflection", "wondered"}):
        return "magical_notice"
    if mood == "magical":
        return "magical_notice"
    if page_number >= page_count - 1 and mood in {"calm", "peaceful", "sleepy"}:
        return "sleepy_settle"
    if "bedroom" in lowered_location and mood in {"calm", "peaceful", "sleepy"}:
        return "sleepy_settle"
    if mood in {"calm", "peaceful", "sleepy"} and page_number > max(2, page_count // 2):
        return "reassuring_connection"
    return "gentle_pause"


def _pick_anchor_prop(*, page_text: str, location: str, existing: list[str], role: str) -> str:
    props = _location_props(location)
    candidates = _dedupe_preserving_order(
        [
            *existing,
            *([_first_matching_object(page_text)] if _first_matching_object(page_text) else []),
            *props,
        ]
    )
    lowered_candidates = {candidate.casefold(): candidate for candidate in candidates}

    preferred_groups = {
        "opening_tableau": ("fort", "sofa", "chair", "mixing bowl", "wooden spoon", "window", "glowing path", "path", "flowers", "lanterns", "books"),
        "magical_notice": ("glowing path", "window", "moon", "lanterns", "flowers"),
        "listening_pause": ("fort", "sofa", "chair", "mixing bowl", "wooden spoon", "flowers", "glowing path", "patchwork blanket", "pillows", "books"),
        "reassuring_connection": ("fort", "sofa", "chair", "mixing bowl", "wooden spoon", "patchwork blanket", "pillows", "flowers", "books", "blankets"),
        "sleepy_settle": ("patchwork blanket", "blanket", "pillows", "basket bed", "cushions", "books"),
        "gentle_pause": ("fort", "sofa", "chair", "sheet", "cushions", "mixing bowl", "wooden spoon", "blueberries", "flour", "books", "flowers", "window", "path"),
    }
    for preferred in preferred_groups.get(role, ()):
        for candidate in candidates:
            if preferred in candidate.casefold():
                return candidate
    if candidates:
        return candidates[0]
    return "the main scene detail"


def _needs_visual_rewrite(*, page_text: str, key_action: str, important_objects: list[str]) -> bool:
    lowered_page = page_text.casefold()
    lowered_action = key_action.casefold()
    if _is_generic_beat_action(key_action):
        return True
    if any(lowered_action.startswith(prefix) for prefix in ABSTRACT_ACTION_PREFIXES):
        return True
    cue_weight = 1 if any(cue in lowered_page for cue in VISUAL_REWRITE_CUES) else 0
    action_hits = sum(1 for token in VISUAL_ACTION_TERMS if re.search(rf"\b{re.escape(token)}\b", lowered_action))
    abstract_hits = sum(1 for token in ABSTRACT_ACTION_TERMS if re.search(rf"\b{re.escape(token)}\b", lowered_action))
    object_hits = sum(1 for label in important_objects if label and label.casefold() in lowered_action)
    if abstract_hits >= 1 and object_hits == 0 and action_hits == 0:
        return True
    if cue_weight and not important_objects and action_hits <= 1:
        return True
    if action_hits == 0:
        return True
    return not important_objects and action_hits <= 1


def _rewrite_visual_action(
    *,
    page_text: str,
    location: str,
    mood: str,
    characters: list[str],
    page_number: int,
    page_count: int,
    existing_objects: list[str],
) -> str:
    lead_name = _lead_character_name(characters)
    others = _other_character_names(characters, lead_name=lead_name)
    others_text = _join_names(others)
    full_group_text = _lead_plus_others_text(lead_name, others)
    pair_text = _join_names(characters) if characters else "the friends"
    role = _select_visual_role(
        page_number=page_number,
        page_count=page_count,
        page_text=page_text,
        mood=mood,
        location=location,
    )
    anchor_prop = _pick_anchor_prop(page_text=page_text, location=location, existing=existing_objects, role=role)
    lowered = page_text.casefold()

    if "kitchen" in location.casefold():
        if any(token in lowered for token in {"mix", "bowl", "batter", "flour", "muffin", "bread", "oven", "blueberry"}):
            if others_text:
                return f"{lead_name} and {others_text} are actively mixing ingredients at the kitchen table beside the {anchor_prop}"
            return f"{pair_text} are actively mixing ingredients at the kitchen table beside the {anchor_prop}"
        return f"{full_group_text} stay clearly inside the kitchen beside the {anchor_prop} while the page action unfolds"
    if "living room" in location.casefold():
        if any(token in lowered for token in {"fort", "forts", "blanket fort", "pillow fort", "den", "sheet", "sofa", "couch"}):
            if others_text:
                return f"{lead_name} and {others_text} are actively building and playing in a homemade fort in the living room beside the {anchor_prop}"
            return f"{pair_text} are actively building and playing in a homemade fort in the living room beside the {anchor_prop}"
        return f"{full_group_text} stay clearly inside the living room beside the {anchor_prop} while the page action unfolds"
    if "reading nook" in location.casefold():
        if others_text:
            return f"{lead_name} and {others_text} are gathered in the reading nook with books and cushions clearly around them"
        return f"{pair_text} are gathered in the reading nook with books and cushions clearly around them"
    if role == "opening_tableau":
        if "window" in anchor_prop.casefold():
            return f"{lead_name} stands by the {anchor_prop} with {others_text}, looking out toward the moonlit garden"
        return f"{full_group_text} gather beside the {anchor_prop} as the bedtime scene opens"
    if role == "sleepy_settle":
        if others_text:
            return f"{lead_name} settles {others_text} beside the {anchor_prop} as the room grows sleepy"
        return f"{pair_text} settle beside the {anchor_prop} as the room grows sleepy"
    if role == "reassuring_connection":
        if others_text:
            return f"{lead_name} shares a warm reassuring look with {others_text} beside the {anchor_prop}"
        return f"{pair_text} share a warm reassuring moment beside the {anchor_prop}"
    if role == "listening_pause":
        if others_text:
            return f"{lead_name} and {others_text} pause close together, listening quietly beside the {anchor_prop}"
        return f"{pair_text} pause close together, listening quietly beside the {anchor_prop}"
    if role == "magical_notice" or any(token in lowered for token in {"kindness", "shine", "magical"}):
        return f"{full_group_text} share a small glowing moment together beside the {anchor_prop}"
    if mood in {"sleepy", "calm", "peaceful"}:
        if others_text:
            return f"{full_group_text} pause in a calm bedtime moment beside the {anchor_prop}"
        return f"{pair_text} pause in a calm bedtime moment beside the {anchor_prop}"
    if mood == "magical":
        if others_text:
            return f"{lead_name} draws {others_text} closer as they notice a magical detail near the {anchor_prop}"
        return f"{pair_text} gather around a magical detail near the {anchor_prop}"
    if others_text:
        return f"{lead_name} shares a gentle bedtime moment with {others_text} beside the {anchor_prop}"
    return f"{pair_text} share one gentle visible bedtime moment beside the {anchor_prop}"


def _rewrite_important_objects(
    *,
    page_text: str,
    location: str,
    existing: list[str],
    page_number: int,
    page_count: int,
    mood: str,
) -> list[str]:
    props = _location_props(location)
    objects: list[str] = list(existing)
    matched = _first_matching_object(page_text)
    if matched and matched not in objects:
        objects.append(matched)
    role = _select_visual_role(
        page_number=page_number,
        page_count=page_count,
        page_text=page_text,
        mood=mood,
        location=location,
    )
    preferred_prop = _pick_anchor_prop(page_text=page_text, location=location, existing=objects, role=role)
    if preferred_prop not in objects:
        objects.append(preferred_prop)
    for prop in _location_required_props(location)[:3]:
        if prop not in objects:
            objects.append(prop)
    for prop in props[:2]:
        if prop not in objects:
            objects.append(prop)
    return _dedupe_preserving_order(objects)[:6]


def _rewrite_composition_note(
    *,
    key_action: str,
    characters: list[str],
    existing: str,
    page_number: int,
    page_count: int,
    page_text: str,
    mood: str,
    location: str,
) -> str:
    role = _select_visual_role(
        page_number=page_number,
        page_count=page_count,
        page_text=page_text,
        mood=mood,
        location=location,
    )
    if role == "opening_tableau":
        return "Opening page composition with the setting clearly established, characters grouped together, and one inviting focal detail"
    if role == "magical_notice":
        return "Center the small magical focal detail and use the characters' shared gaze to make the page read instantly"
    if role == "listening_pause":
        return "Use a quiet clustered composition with listening body language and a soft environmental focal point"
    if role == "reassuring_connection":
        return "Use a close comforting composition with one clear caring gesture and supportive reactions"
    if role == "sleepy_settle":
        return "Closing or settling composition with blanket-level warmth, restful spacing, and simple bedtime props"
    lowered_action = key_action.casefold()
    if any(token in lowered_action for token in {"pause", "settle"}):
        return "Keep the characters grouped in one calm readable cluster with a single soothing focal point"
    if len(characters) == 2:
        return "Use a two-character bedside composition with one clear comforting gesture and simple supporting props"
    return existing


def _derive_key_action(page_text: str, beat: IllustrationScene | None) -> str:
    page_action = _best_visual_sentence(page_text)
    if beat is not None and beat.action:
        beat_action = beat.action.strip().rstrip(".")
        if not _is_generic_beat_action(beat_action):
            return beat_action
    if page_action:
        return page_action.rstrip(".")
    return "Show the strongest visible story moment on this page"


def _important_objects(page_text: str, beat: IllustrationScene | None) -> list[str]:
    lowered = page_text.casefold()
    objects: list[str] = []
    for label, keywords in OBJECT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            objects.append(label)
    if beat is not None:
        for item in beat.must_show:
            cleaned = item.strip()
            if cleaned and not _is_generic_beat_action(cleaned) and cleaned not in objects:
                objects.append(cleaned)
    return _dedupe_preserving_order(objects)[:6]


def _lighting_note(*, location: str, mood: str, characters: list[str], beat: IllustrationScene | None) -> str:
    lowered_location = location.casefold()
    lowered_mood = mood.casefold()
    parts: list[str] = []
    if "bedroom" in lowered_location or "window" in lowered_location or "house" in lowered_location:
        parts.append("warm bedside lamp glow with soft blue moonlight through the window")
    elif "living room" in lowered_location:
        parts.append("warm indoor family-room light with clear cozy evening visibility, not bedroom lighting")
    elif "garden" in lowered_location or "pond" in lowered_location or "meadow" in lowered_location:
        parts.append("soft moonlight with gentle glow on flowers and grass")
    else:
        parts.append("soft bedtime cinematic lighting with clear focal glow")
    if "buddybug" in {item.casefold() for item in characters}:
        parts.append("Buddybug adds a warm golden magical glow near the main action")
    if beat is not None and beat.emotion and "surprise" in beat.emotion.casefold():
        parts.append("keep the lighting playful and readable rather than dramatic")
    elif lowered_mood in {"calm", "sleepy", "peaceful", "comforting", "dreamy"}:
        parts.append("keep the light calm, safe, and bedtime-friendly")
    return "; ".join(parts)


def _composition_note(*, page_number: int, page_count: int, characters: list[str], beat: IllustrationScene | None) -> str:
    character_count = len(characters)
    if beat is not None and beat.action:
        action = beat.action.casefold()
        if any(token in action for token in ["reveal", "found", "shows", "opened", "looked"]):
            return "Center the single reveal moment with the key object clearly visible and supporting reactions around it"
        if any(token in action for token in ["leapt", "ran", "splash", "chased", "jumped"]):
            return "Use a storybook action composition with one main movement beat and clear readable silhouettes"
    if page_number == 1:
        return "Opening page composition with a clear focal subject, strong mood, and inviting storybook framing"
    if page_number == page_count:
        return "Closing page composition with warm restful balance and gentle settling body language"
    if character_count >= 3:
        return "Medium-close storybook composition with one main focal action and the rest supporting it without crowding the frame"
    if character_count == 2:
        return "Use a two-character composition with one acting and one reacting so the page reads instantly"
    return "Keep one main visual moment centered with clean foreground focus and simple supporting background detail"


def _continuity_notes(*, characters: list[str], beat: IllustrationScene | None, previous_page_text: str | None) -> list[str]:
    notes: list[str] = []
    lowered_characters = {item.casefold() for item in characters}
    if "daphne" in lowered_characters:
        notes.append("Daphne keeps her black-and-tan dachshund markings, red collar, and gold star tag")
    if "dolly" in lowered_characters:
        notes.append("Dolly keeps her grey dapple coat, blue collar, and slightly gentler face shape")
    if "verity" in lowered_characters:
        notes.append("Verity keeps her long golden blonde hair, white dress, and warm expressive eyes")
    if "buddybug" in lowered_characters:
        notes.append("Buddybug stays a small glowing golden firefly with a friendly face and warm light")
    if beat is not None:
        notes.extend(_dedupe_preserving_order(beat.continuity_notes))
    previous_excerpt = _context_excerpt(previous_page_text)
    if previous_excerpt:
        notes.append(f"Maintain continuity from previous page: {previous_excerpt}")
    return _dedupe_preserving_order(notes)


def _build_page_brief(
    *,
    page_number: int,
    page_count: int,
    page_text: str,
    location: str,
    mood: str,
    characters: list[str],
    previous_page_text: str | None,
    beat: IllustrationScene | None,
) -> IllustrationPageBrief:
    key_action = _derive_key_action(page_text, beat)
    important_objects = _important_objects(page_text, beat)
    composition_note = _composition_note(
        page_number=page_number,
        page_count=page_count,
        characters=characters,
        beat=beat,
    )
    if _needs_visual_rewrite(page_text=page_text, key_action=key_action, important_objects=important_objects):
        key_action = _rewrite_visual_action(
            page_text=page_text,
            location=location,
            mood=mood,
            characters=characters,
            page_number=page_number,
            page_count=page_count,
            existing_objects=important_objects,
        )
        important_objects = _rewrite_important_objects(
            page_text=page_text,
            location=location,
            existing=important_objects,
            page_number=page_number,
            page_count=page_count,
            mood=mood,
        )
        composition_note = _rewrite_composition_note(
            key_action=key_action,
            characters=characters,
            existing=composition_note,
            page_number=page_number,
            page_count=page_count,
            page_text=page_text,
            mood=mood,
            location=location,
        )
    return IllustrationPageBrief(
        page_number=page_number,
        exact_text=page_text.strip(),
        scene_location=location,
        characters_present=characters,
        key_action=key_action,
        emotional_tone=beat.emotion if beat is not None and beat.emotion else mood,
        important_objects=important_objects,
        time_of_day_lighting=_lighting_note(location=location, mood=mood, characters=characters, beat=beat),
        composition_note=composition_note,
        continuity_notes=_continuity_notes(
            characters=characters,
            beat=beat,
            previous_page_text=previous_page_text,
        ),
    )


def _beat_for_page(illustration_beats: list[IllustrationScene], *, page_index: int, page_count: int) -> IllustrationScene | None:
    if not illustration_beats or page_count <= 0:
        return None
    beat_index = min(len(illustration_beats) - 1, ((page_index - 1) * len(illustration_beats)) // page_count)
    return illustration_beats[beat_index]


def _illustration_prompt(
    *,
    brief: IllustrationPageBrief,
    scene_summary: str,
    style_suffix: str,
    previous_page_text: str | None = None,
    next_page_text: str | None = None,
    beat: IllustrationScene | None = None,
) -> str:
    focus_characters = brief.characters_present or (beat.focus_characters if beat is not None else [])
    primary_focus_text = ", ".join(focus_characters) if focus_characters else "gentle bedtime scene"
    present_characters_text = (
        ", ".join(brief.characters_present)
        if brief.characters_present
        else primary_focus_text
    )
    lines = [
        "Create one children's storybook illustration for a single story page.",
        "Pick one main visual moment only. Do not try to show the whole page at once.",
        f"Page number: {brief.page_number}",
        f"Exact text: {brief.exact_text}",
        f"Scene location: {brief.scene_location}",
        f"This scene must be clearly and unmistakably set in {brief.scene_location}.",
        f"Characters present: {present_characters_text}.",
        f"Key action: {brief.key_action}.",
        f"Emotional tone: {brief.emotional_tone}.",
        f"Important objects: {', '.join(brief.important_objects) if brief.important_objects else 'none beyond the main action'}.",
        f"Time of day and lighting: {brief.time_of_day_lighting}.",
        f"Composition note: {brief.composition_note}.",
        f"Continuity notes: {'; '.join(brief.continuity_notes)}.",
        f"Primary focus characters: {primary_focus_text}.",
        f"Scene summary: {scene_summary}",
    ]
    previous_excerpt = _context_excerpt(previous_page_text)
    if previous_excerpt:
        lines.append(f"Previous page context: {previous_excerpt}")
    next_excerpt = _context_excerpt(next_page_text)
    if next_excerpt:
        lines.append(f"Next page context: {next_excerpt}")
    if beat is not None:
        lines.append(f"Story beat: {beat.label}.")
        if beat.action:
            lines.append(f"Visible action to show: {beat.action}")
        if beat.emotion:
            lines.append(f"Emotion to convey: {beat.emotion}.")
        if beat.location_hint:
            lines.append(f"Location hint: {beat.location_hint}.")
        if beat.must_show:
            lines.append(f"Must show: {'; '.join(_dedupe_preserving_order(beat.must_show))}.")
        if beat.continuity_notes:
            lines.append(f"Continuity notes: {' '.join(_dedupe_preserving_order(beat.continuity_notes))}")
    required_location_props = _location_required_props(brief.scene_location)
    if required_location_props:
        lines.append(f"Required setting anchors: {'; '.join(required_location_props)}.")
    location_negative_lines = _location_negative_elements(brief.scene_location)
    if location_negative_lines:
        lines.append(f"Do not relocate this scene: {'; '.join(location_negative_lines)}.")
    location_lines = build_location_visual_lines(brief.scene_location)
    if location_lines:
        lines.append("Location canon:")
        lines.extend(location_lines)
    character_lines = build_character_visual_lines(focus_characters)
    if character_lines:
        lines.append("Character canon:")
        lines.extend(character_lines)
    negative_lines = [
        "Keep the image aligned to this exact adjacent page beat, not the whole story at once.",
        "Show specific readable action with clean composition and child-friendly expressions.",
        "No text, captions, letters, labels, watermarks, or readable writing anywhere inside the artwork.",
    ]
    negative_lines.extend(location_negative_lines)
    if beat is not None and beat.must_not_show:
        negative_lines.extend(_dedupe_preserving_order(beat.must_not_show))
    lines.append(f"Style: {style_suffix}.")
    lines.append(f"Negative prompt: {'; '.join(_dedupe_preserving_order(negative_lines))}.")
    return "\n".join(lines)


def generate_story_page_payloads(
    *,
    story_draft: StoryDraft,
    story_idea: StoryIdea | None = None,
    target_page_count: int | None,
    min_pages: int,
    max_pages: int,
) -> list[dict[str, str | int | None]]:
    """Create ordered page plans for an approved story draft.

    Existing pages should be deleted by the caller before saving a new plan.
    """
    source_text = _source_text(story_draft)
    units = _prepare_units(source_text)
    word_count = len(source_text.split())
    page_count = _choose_target_page_count(word_count, target_page_count, min_pages, max_pages)
    pages = _chunk_units(units, page_count)
    outline = build_story_outline(story_idea) if story_idea is not None else None
    illustration_scenes = build_illustration_scenes(story_idea, outline) if story_idea is not None and outline is not None else []
    fallback_location = story_idea.setting if story_idea is not None else "cozy bedroom"
    default_characters = _detect_characters(source_text)
    style_suffix = _style_suffix_for_story(story_idea)

    payloads: list[dict[str, str | int | None]] = []
    for index, page_text in enumerate(pages, start=1):
        beat = _beat_for_page(illustration_scenes, page_index=index, page_count=len(pages))
        location = _infer_location(page_text, fallback_location)
        mood = _infer_mood(page_text)
        if beat is not None and beat.key in {"scene_1", "scene_5"} and story_idea is not None and "playful" not in (story_idea.tone or "").casefold():
            mood = "calm"
        if beat is not None and beat.key == "scene_3" and story_idea is not None and "playful" in (story_idea.tone or "").casefold():
            mood = "gently curious"
        characters = _detect_characters(page_text) or default_characters
        scene_summary = _scene_summary(page_text, location, mood, beat=beat)
        brief = _build_page_brief(
            page_number=index,
            page_count=len(pages),
            page_text=page_text,
            location=location,
            mood=mood,
            characters=characters,
            previous_page_text=pages[index - 2] if index > 1 else None,
            beat=beat,
        )
        illustration_prompt = _illustration_prompt(
            brief=brief,
            scene_summary=scene_summary,
            style_suffix=style_suffix,
            previous_page_text=pages[index - 2] if index > 1 else None,
            next_page_text=pages[index] if index < len(pages) else None,
            beat=beat,
        )
        payloads.append(
            {
                "story_draft_id": story_draft.id,
                "page_number": index,
                "page_text": page_text,
                "scene_summary": scene_summary,
                "location": location,
                "mood": mood,
                "characters_present": ", ".join(characters),
                "illustration_prompt": illustration_prompt,
                "image_status": "prompt_ready",
                "image_url": None,
            }
        )

    return payloads
