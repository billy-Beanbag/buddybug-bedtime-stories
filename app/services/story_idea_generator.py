from __future__ import annotations

import logging
import random
import secrets
from dataclasses import dataclass

from app.services.content_lane_service import resolve_content_lane_key
from app.services.story_engine_data import (
    ADVENTURE_FEELINGS,
    ADVENTURE_SETTINGS,
    ADVENTURE_THEMES,
    BEDTIME_ALLOWED_HOOK_KEYS,
    BEDTIME_FEELINGS,
    BEDTIME_MODE,
    BEDTIME_SETTINGS,
    BEDTIME_THEMES,
    DEFAULT_ADVENTURE_TONE,
    DEFAULT_BEDTIME_TONE,
    DEFAULT_STANDARD_TONE,
    STANDARD_3_7_FEELINGS,
    STANDARD_3_7_SETTINGS,
    STANDARD_3_7_THEMES,
    STANDARD_ALLOWED_HOOK_KEYS,
    STANDARD_MODE,
)
from app.utils.seed_content_lanes import STORY_ADVENTURES_8_12_LANE_KEY

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IdeaGenerationResult:
    """Structured idea batch plus how it was produced (for API / admin diagnostics)."""

    payloads: list[dict[str, str | int | None]]
    path: str  # "llm" | "llm_plus_curated" | "curated"
    excluded_premise_count: int
    llm_idea_count: int
    curated_idea_count: int


from app.services.curated_story_premises import (
    CURATED_PREMISES,
    curated_hook_for_index,
    title_from_curated_premise,
)

CANONICAL_CHARACTER_ORDER = [
    "Verity",
    "Dolly",
    "Daphne",
    "Buddybug",
    "Glowmoth",
    "Twinklet",
    "Whisperwing",
]

SERIES_DEFINITIONS = [
    {
        "key": "dolly_daphne",
        "title": "Dolly & Daphne",
        "characters": {"Dolly", "Daphne", "Verity"},
    },
    {
        "key": "buddybug_storylight_guardians",
        "title": "Buddybug & the Storylight Guardians",
        "characters": {"Buddybug", "Glowmoth", "Twinklet", "Whisperwing"},
    },
    {
        "key": "calamitous_robot",
        "title": "Calamitous Robot",
        "characters": set(),
    },
    {
        "key": "garden_league_insects",
        "title": "Garden League Insects",
        "characters": {"Buddybug", "Glowmoth", "Twinklet", "Whisperwing"},
    },
]


def _split_names(raw_names: str | None) -> list[str]:
    if not raw_names:
        return []
    return [name.strip() for name in raw_names.split(",") if name.strip()]


def _infer_mode(*, lane_key: str, bedtime_only: bool, tone: str) -> str:
    normalized_tone = (tone or "").casefold()
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return STANDARD_MODE
    if bedtime_only:
        return BEDTIME_MODE
    if any(token in normalized_tone for token in {"playful", "cheeky", "mischief", "fun", "humour", "humor"}):
        return STANDARD_MODE
    return BEDTIME_MODE


def _resolved_tone(*, mode: str, lane_key: str, tone: str) -> str:
    normalized_tone = tone.strip().casefold()
    if normalized_tone and normalized_tone not in {"calming, dreamy, gentle", "dreamy, gentle", "gentle, dreamy"}:
        return tone
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return DEFAULT_ADVENTURE_TONE
    return DEFAULT_BEDTIME_TONE if mode == BEDTIME_MODE else DEFAULT_STANDARD_TONE


def _choose_characters(
    *,
    available_characters: list[str],
    include_characters: list[str] | None,
    index: int,
    mode: str,
) -> tuple[list[str], list[str]]:
    ordered = [name for name in CANONICAL_CHARACTER_ORDER if name in available_characters] or list(available_characters)
    if include_characters:
        normalized = {name.casefold(): name for name in ordered}
        chosen = [normalized[name.casefold()] for name in include_characters if name.casefold() in normalized]
        if chosen:
            ordered = list(dict.fromkeys(chosen + [name for name in ordered if name not in chosen]))

    main_count = 2 if ordered else 0
    support_count = 1 if mode == BEDTIME_MODE else 2
    main_characters = [ordered[(index + offset) % len(ordered)] for offset in range(main_count)] if ordered else []
    support_candidates = [name for name in ordered if name not in main_characters]
    supporting_characters = support_candidates[:support_count]
    return main_characters, supporting_characters


def _choose_setting(*, mode: str, lane_key: str, index: int) -> str:
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        options = ADVENTURE_SETTINGS
    elif mode == BEDTIME_MODE:
        options = BEDTIME_SETTINGS
    else:
        options = STANDARD_3_7_SETTINGS
    return options[index % len(options)]


def _choose_theme(*, mode: str, lane_key: str, index: int) -> str:
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        options = ADVENTURE_THEMES
    elif mode == BEDTIME_MODE:
        options = BEDTIME_THEMES
    else:
        options = STANDARD_3_7_THEMES
    return options[index % len(options)]


def _choose_feeling(*, mode: str, lane_key: str, index: int) -> str:
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        options = ADVENTURE_FEELINGS
    elif mode == BEDTIME_MODE:
        options = BEDTIME_FEELINGS
    else:
        options = STANDARD_3_7_FEELINGS
    return options[index % len(options)]


def _series_for_characters(main_characters: list[str], supporting_characters: list[str]) -> tuple[str | None, str | None]:
    combined = set(main_characters + supporting_characters)
    for series in SERIES_DEFINITIONS:
        characters = series["characters"]
        if not characters:
            continue
        if combined & characters:
            return str(series["key"]), str(series["title"])
    return None, None


def _missing_item_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "bedroom" in lowered:
        return "her patchwork blanket"
    if "garden" in lowered:
        return "the little lantern ribbon"
    if "hallway" in lowered:
        return "the bedtime songbook"
    return "the small comfort pillow"


def _creature_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "garden" in lowered or "meadow" in lowered:
        return "a tiny frog"
    if "bedroom" in lowered:
        return "a fluttery moth"
    return "a little field mouse"


def _clue_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "bedroom" in lowered:
        return "a loose thread near the rocking chair"
    if "garden" in lowered or "path" in lowered:
        return "odd little marks by the path"
    if "reading nook" in lowered:
        return "a folded note tucked into the wrong book"
    return "a curious clue in the wrong place"


def _plan_task_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "reading nook" in lowered:
        return "stacking the books before story time"
    if "toy cupboard" in lowered:
        return "putting the toys away in a hurry"
    if "kitchen" in lowered:
        return "carrying cups and napkins to the table"
    return "tidying up before the next part of the day"


def _mess_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "kitchen" in lowered:
        return "a bowl of blueberry batter"
    if "picnic" in lowered or "puddle" in lowered:
        return "a picnic basket wobbling near a puddle"
    return "a stack of teacups"


def _competition_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "puddle" in lowered or "picnic" in lowered or "garden" in lowered or "path" in lowered:
        return "who could hop over the biggest puddle"
    return "who could carry the most things at once"


def _premise_for_hook(
    *,
    hook_type: str,
    main_characters: list[str],
    supporting_characters: list[str],
    setting: str,
) -> str:
    lead = main_characters[0] if main_characters else "Someone"
    pair = _join_names(main_characters)
    helper = supporting_characters[0] if supporting_characters else "their friend"
    if hook_type == "missing_item":
        return f"{lead} discovers that {_missing_item_for_setting(setting)} has gone missing in the {setting}."
    if hook_type == "clever_shortcut":
        return f"{lead} believes there is a clever shortcut through the {setting}, but it sends {pair} the wrong way."
    if hook_type == "accidental_mess":
        return f"{pair} turn {_mess_for_setting(setting)} into a funny muddle in the {setting}."
    if hook_type == "tiny_creature_problem":
        return f"{pair} find {_creature_for_setting(setting)} beside the wrong thing and have to help it gently."
    if hook_type == "misunderstanding":
        return f"{pair} notice {_clue_for_setting(setting)} and make different guesses about what it means."
    if hook_type == "helpful_plan_goes_wrong":
        return f"{lead} tries to help by {_plan_task_for_setting(setting)}, but the sensible plan turns into a wobbling muddle."
    if hook_type == "silly_competition":
        return f"{pair} get distracted by { _competition_for_setting(setting) } and turn a tiny contest into a funny problem."
    if hook_type == "unexpected_discovery":
        return f"{pair} notice {_clue_for_setting(setting)} in the {setting} and decide they must find out what happened."
    if hook_type == "pretend_game":
        return f"{pair} get carried away with a pretend game in the {setting} until it causes a real little problem."
    return f"{pair} notice that one small part of the {setting} is not quite right and decide to sort it out together."


def _title_for_hook(hook_type: str, main_characters: list[str], setting: str) -> str:
    lead = main_characters[0] if main_characters else "Buddybug"
    second = main_characters[1] if len(main_characters) > 1 else lead
    if hook_type == "missing_item":
        return f"{lead} and the Missing Blanket Trail"
    if hook_type == "clever_shortcut":
        return f"{lead} and the Garden Shortcut" if "garden" in setting.casefold() else f"{lead} and the Clever Shortcut"
    if hook_type == "accidental_mess":
        return f"{lead}, {second}, and the Funny Muddle"
    if hook_type == "tiny_creature_problem":
        return f"{lead} and the Tiny Visitor"
    if hook_type == "misunderstanding":
        return f"{lead} and {second}'s Mixed-Up Clue"
    if hook_type == "helpful_plan_goes_wrong":
        return "The Reading Nook Plan" if "reading nook" in setting.casefold() else f"{lead}'s Helpful Plan"
    if hook_type == "silly_competition":
        return f"{lead} and {second}'s Puddle Contest" if "puddle" in setting.casefold() else f"{lead} and {second}'s Silly Contest"
    if hook_type == "unexpected_discovery":
        return f"{lead} and the Strange Find"
    if hook_type == "pretend_game":
        return f"{lead} and {second}'s Pretend-Day Problem"
    return f"{lead} and the Gentle Problem"


def _normalize_premise_key(premise: str) -> str:
    return premise.strip().casefold()


def _pick_curated_premise_indices(*, count: int, exclude_normalized: set[str]) -> list[int]:
    """Pick premise line indices, strongly preferring lines not in exclude_normalized."""
    n = len(CURATED_PREMISES)
    preferred = [i for i, p in enumerate(CURATED_PREMISES) if _normalize_premise_key(p) not in exclude_normalized]
    rng = random.Random(secrets.token_bytes(16))
    if len(preferred) >= count:
        rng.shuffle(preferred)
        return preferred[:count]
    out: list[int] = []
    if preferred:
        rng.shuffle(preferred)
        out.extend(preferred)
    need = count - len(out)
    used = set(out)
    second = [
        i
        for i in range(n)
        if i not in used and _normalize_premise_key(CURATED_PREMISES[i]) not in exclude_normalized
    ]
    if len(second) < need:
        second = [i for i in range(n) if i not in used]
    rng.shuffle(second)
    for j in range(need):
        out.append(second[j % len(second)])
    return out[:count]


def generate_story_idea_payloads(
    *,
    count: int,
    age_band: str,
    content_lane_key: str | None,
    tone: str,
    include_characters: list[str] | None,
    bedtime_only: bool,
    available_characters: list[str],
    exclude_premises: frozenset[str] | None = None,
    exclude_premise_hints: tuple[str, ...] | None = None,
    editorial_guidance: tuple[str, ...] | None = None,
) -> IdeaGenerationResult:
    """Generate short, hook-first Buddybug ideas for the structured story pipeline."""
    lane_key = resolve_content_lane_key(age_band, content_lane_key)
    mode = _infer_mode(lane_key=lane_key, bedtime_only=bedtime_only, tone=tone)
    resolved_tone = _resolved_tone(mode=mode, lane_key=lane_key, tone=tone)
    exclude_norm: set[str] = set(exclude_premises) if exclude_premises else set()
    excluded_n = len(exclude_norm)

    # Prefer LLM when configured (same STORY_GENERATION_* env as full-story generation).
    try:
        from app.config import (
            STORY_GENERATION_API_KEY,
            STORY_GENERATION_MODEL,
            STORY_IDEA_GENERATION_USE_LLM,
        )
        from app.services.story_idea_llm import try_generate_llm_idea_payloads

        if (
            STORY_IDEA_GENERATION_USE_LLM
            and STORY_GENERATION_API_KEY.strip()
            and STORY_GENERATION_MODEL.strip()
        ):
            llm_payloads = try_generate_llm_idea_payloads(
                count=count,
                age_band=age_band,
                content_lane_key=lane_key,
                resolved_tone=resolved_tone,
                mode=mode,
                available_characters=available_characters,
                exclude_premises_normalized=exclude_norm,
                exclude_premise_hints=exclude_premise_hints,
                editorial_guidance=editorial_guidance,
            )
            if llm_payloads is not None and len(llm_payloads) >= count:
                pl = llm_payloads[:count]
                logger.info(
                    "story_ideas: returning %s llm_generated_idea rows (lane=%s)",
                    len(pl),
                    lane_key,
                )
                return IdeaGenerationResult(
                    payloads=pl,
                    path="llm",
                    excluded_premise_count=excluded_n,
                    llm_idea_count=len(pl),
                    curated_idea_count=0,
                )
            if llm_payloads and len(llm_payloads) > 0:
                # Partial batch: top up with curated so the UI always gets `count` rows.
                need = count - len(llm_payloads)
                extra_exclude = set(exclude_norm)
                for row in llm_payloads:
                    pr = row.get("premise")
                    if isinstance(pr, str) and pr.strip():
                        extra_exclude.add(_normalize_premise_key(pr))
                curated_extra = _generate_curated_premise_payloads(
                    count=need,
                    age_band=age_band,
                    lane_key=lane_key,
                    mode=mode,
                    resolved_tone=resolved_tone,
                    include_characters=include_characters,
                    available_characters=available_characters,
                    start_index=len(llm_payloads),
                    exclude_premises_normalized=extra_exclude,
                )
                logger.info(
                    "story_ideas: partial llm (%s) + curated (%s) (lane=%s)",
                    len(llm_payloads),
                    need,
                    lane_key,
                )
                combined = [*llm_payloads, *curated_extra]
                return IdeaGenerationResult(
                    payloads=combined,
                    path="llm_plus_curated",
                    excluded_premise_count=excluded_n,
                    llm_idea_count=len(llm_payloads),
                    curated_idea_count=len(curated_extra),
                )
            logger.warning(
                "story_ideas: llm returned no usable rows; curated fallback (lane=%s exclude=%s)",
                lane_key,
                len(exclude_norm),
            )
    except Exception:
        logger.exception("LLM idea generation path failed; using curated premises")

    logger.info(
        "story_ideas: curated_premise batch count=%s lane=%s exclude=%s",
        count,
        lane_key,
        len(exclude_norm),
    )
    curated = _generate_curated_premise_payloads(
        count=count,
        age_band=age_band,
        lane_key=lane_key,
        mode=mode,
        resolved_tone=resolved_tone,
        include_characters=include_characters,
        available_characters=available_characters,
        start_index=0,
        exclude_premises_normalized=exclude_norm,
    )
    return IdeaGenerationResult(
        payloads=curated,
        path="curated",
        excluded_premise_count=excluded_n,
        llm_idea_count=0,
        curated_idea_count=len(curated),
    )


def _generate_curated_premise_payloads(
    *,
    count: int,
    age_band: str,
    lane_key: str,
    mode: str,
    resolved_tone: str,
    include_characters: list[str] | None,
    available_characters: list[str],
    start_index: int,
    exclude_premises_normalized: set[str] | None = None,
) -> list[dict[str, str | int | None]]:
    payloads: list[dict[str, str | int | None]] = []
    ex = exclude_premises_normalized or set()
    premise_indices = _pick_curated_premise_indices(count=count, exclude_normalized=ex)

    for index in range(count):
        slot = start_index + index
        main_characters, supporting_characters = _choose_characters(
            available_characters=available_characters,
            include_characters=include_characters,
            index=slot,
            mode=mode,
        )
        setting = _choose_setting(mode=mode, lane_key=lane_key, index=slot)
        theme = _choose_theme(mode=mode, lane_key=lane_key, index=slot)
        bedtime_feeling = _choose_feeling(mode=mode, lane_key=lane_key, index=slot)
        premise_index = premise_indices[index]
        premise = CURATED_PREMISES[premise_index]
        hook_type = curated_hook_for_index(premise_index, mode=mode)
        series_key, series_title = _series_for_characters(main_characters, supporting_characters)
        payloads.append(
            {
                "title": title_from_curated_premise(premise),
                "premise": premise,
                "hook_type": hook_type,
                "age_band": age_band,
                "content_lane_key": lane_key,
                "tone": resolved_tone,
                "setting": setting,
                "theme": theme,
                "bedtime_feeling": bedtime_feeling,
                "main_characters": ", ".join(main_characters),
                "supporting_characters": ", ".join(supporting_characters) or None,
                "series_key": series_key,
                "series_title": series_title,
                "estimated_minutes": 7 if mode == BEDTIME_MODE else 6,
                "status": "idea_pending",
                "generation_source": "curated_premise",
            }
        )
    return payloads
