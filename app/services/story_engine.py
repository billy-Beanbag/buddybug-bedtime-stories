from __future__ import annotations

from app.models import StoryIdea
from app.schemas.story_engine_schema import StoryBeat, StoryPlan, StoryPromptContext
from app.services.content_lane_service import resolve_content_lane_key
from app.services.story_engine_data import (
    ADVENTURE_FEELINGS,
    ADVENTURE_MINUTES,
    ADVENTURE_SETTINGS,
    ADVENTURE_THEMES,
    BEDTIME_ALLOWED_HOOK_KEYS,
    BEDTIME_FEELINGS,
    BEDTIME_MINUTES,
    BEDTIME_MODE,
    BEDTIME_SETTINGS,
    BEDTIME_THEMES,
    CHARACTER_BEHAVIOUR,
    DEFAULT_ADVENTURE_TONE,
    DEFAULT_BEDTIME_TONE,
    DEFAULT_STANDARD_TONE,
    HOOK_DEFINITIONS,
    STANDARD_3_7_FEELINGS,
    STANDARD_3_7_MINUTES,
    STANDARD_3_7_SETTINGS,
    STANDARD_3_7_THEMES,
    STANDARD_ALLOWED_HOOK_KEYS,
    STANDARD_MODE,
)
from app.utils.seed_content_lanes import BEDTIME_3_7_LANE_KEY, STORY_ADVENTURES_8_12_LANE_KEY

CANONICAL_CHARACTER_ORDER = [
    "Verity",
    "Dolly",
    "Daphne",
    "Buddybug",
    "Glowmoth",
    "Twinklet",
    "Whisperwing",
]


def get_allowed_hooks_for_mode(mode: str) -> list[str]:
    if mode == BEDTIME_MODE:
        return list(BEDTIME_ALLOWED_HOOK_KEYS)
    return list(STANDARD_ALLOWED_HOOK_KEYS)


def _split_names(raw_names: str | None) -> list[str]:
    if not raw_names:
        return []
    return [name.strip() for name in raw_names.split(",") if name.strip()]


def _join_names(names: list[str]) -> str:
    if not names:
        return "their friends"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def _leading_cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _theme_phrase(theme: str) -> str:
    phrases = {
        "kindness": "kindness matters in the small choices that solve a problem",
        "sharing": "sharing works best when everyone explains what they need",
        "bravery": "quiet bravery can solve ordinary worries",
        "calmness": "staying calm helps everyone notice the real answer",
        "curiosity": "curiosity works best when it follows a real clue",
        "bedtime routine": "every bedtime step has a purpose",
        "feeling safe at night": "feeling safe grows when the unknown is gently explained",
        "teamwork": "teamwork turns a muddle into progress",
        "problem solving": "problem solving happens one careful step at a time",
        "courage": "courage can be steady and thoughtful",
        "friendship": "friendship helps little misunderstandings shrink quickly",
        "responsibility": "responsibility means finishing the helpful thing you started",
        "hope": "hope gives everyone a reason to keep looking kindly",
    }
    return phrases.get(theme, theme)


def _default_tone_for_mode(mode: str, lane_key: str) -> str:
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return DEFAULT_ADVENTURE_TONE
    if mode == BEDTIME_MODE:
        return DEFAULT_BEDTIME_TONE
    return DEFAULT_STANDARD_TONE


def _infer_mode(*, age_band: str, content_lane_key: str | None, bedtime_only: bool, tone: str | None) -> str:
    lane_key = resolve_content_lane_key(age_band, content_lane_key)
    normalized_tone = (tone or "").lower()
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return STANDARD_MODE
    if bedtime_only:
        return BEDTIME_MODE
    if any(token in normalized_tone for token in ["playful", "cheeky", "mischief", "fun"]):
        return STANDARD_MODE
    return BEDTIME_MODE


def choose_story_characters(
    *,
    available_characters: list[str],
    include_characters: list[str] | None = None,
    mode: str,
    index: int = 0,
) -> tuple[list[str], list[str]]:
    available_lookup = {name.casefold(): name for name in available_characters}
    ordered = [name for name in CANONICAL_CHARACTER_ORDER if name in available_characters]
    if not ordered:
        ordered = available_characters
    if include_characters:
        selected = [available_lookup[name.strip().casefold()] for name in include_characters if name.strip().casefold() in available_lookup]
        if selected:
            ordered = list(dict.fromkeys(selected + [name for name in ordered if name not in selected]))

    main_count = 2 if mode == BEDTIME_MODE else 2
    support_count = 1 if mode == BEDTIME_MODE else 2
    main_characters = [ordered[(index + offset) % len(ordered)] for offset in range(main_count)]
    support_candidates = [name for name in ordered if name not in main_characters]
    supporting_characters = support_candidates[:support_count]
    return main_characters, supporting_characters


def choose_story_setting(*, mode: str, lane_key: str, index: int = 0, explicit_setting: str | None = None) -> str:
    if explicit_setting:
        return explicit_setting
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        options = ADVENTURE_SETTINGS
    elif mode == BEDTIME_MODE:
        options = BEDTIME_SETTINGS
    else:
        options = STANDARD_3_7_SETTINGS
    return options[index % len(options)]


def _choose_story_theme(*, mode: str, lane_key: str, index: int = 0, explicit_theme: str | None = None) -> str:
    if explicit_theme:
        return explicit_theme
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        options = ADVENTURE_THEMES
    elif mode == BEDTIME_MODE:
        options = BEDTIME_THEMES
    else:
        options = STANDARD_3_7_THEMES
    return options[index % len(options)]


def _choose_story_feeling(*, mode: str, lane_key: str, index: int = 0, explicit_feeling: str | None = None) -> str:
    if explicit_feeling:
        return explicit_feeling
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        options = ADVENTURE_FEELINGS
    elif mode == BEDTIME_MODE:
        options = BEDTIME_FEELINGS
    else:
        options = STANDARD_3_7_FEELINGS
    return options[index % len(options)]


def _supports_hook(character: str, hook_key: str) -> int:
    profile = CHARACTER_BEHAVIOUR.get(character)
    if profile is None:
        return 0
    preferred = profile.get("preferred_hooks", [])
    return 2 if hook_key in preferred else 0


def choose_story_hook(
    *,
    mode: str,
    main_characters: list[str],
    supporting_characters: list[str],
    theme: str,
    index: int = 0,
) -> str:
    allowed_hooks = get_allowed_hooks_for_mode(mode)
    all_characters = main_characters + supporting_characters
    scored_hooks: list[tuple[int, int, str]] = []
    for offset, hook_key in enumerate(allowed_hooks):
        score = 0
        score += sum(_supports_hook(character, hook_key) for character in all_characters)
        if theme == "problem solving" and hook_key in {"helpful_plan_goes_wrong", "clever_shortcut", "missing_item"}:
            score += 1
        if theme == "responsibility" and hook_key in {"helpful_plan_goes_wrong", "missing_item"}:
            score += 3
        if theme == "friendship" and hook_key in {"misunderstanding", "pretend_game", "silly_competition"}:
            score += 3
        if theme == "teamwork" and hook_key in {"helpful_plan_goes_wrong", "silly_competition", "pretend_game"}:
            score += 3
        if theme in {"curiosity", "hope"} and hook_key in {"unexpected_discovery", "tiny_creature_problem"}:
            score += 1
        if mode == STANDARD_MODE and "Daphne" in main_characters and hook_key in {"clever_shortcut", "accidental_mess", "silly_competition"}:
            score += 2
        scored_hooks.append((-(score), (index + offset) % len(allowed_hooks), hook_key))
    scored_hooks.sort()
    return scored_hooks[0][2]


def _story_problem_text(hook_key: str, *, setting: str, catalyst: str, gentle_friend: str) -> str:
    return {
        "missing_item": f"something important has gone missing in the {setting}",
        "clever_shortcut": f"{catalyst} insists there is a quicker way through the {setting}",
        "accidental_mess": f"a harmless splash or tumble has turned the {setting} into a funny mess",
        "tiny_creature_problem": f"a tiny creature in the {setting} has borrowed the wrong thing",
        "misunderstanding": f"{gentle_friend} and {catalyst} have made different guesses about the same clue",
        "helpful_plan_goes_wrong": f"a helpful plan has started well and then become a bigger muddle",
        "silly_competition": f"a silly contest has created an unexpected problem to solve",
        "unexpected_discovery": f"something odd has appeared in the {setting} that clearly was not there before",
        "pretend_game": f"a pretend game has caused a real little problem in the {setting}",
        "gentle_problem": f"something in the {setting} is quietly out of place",
    }.get(hook_key, f"a small mystery has appeared in the {setting}")


def _story_goal_text(hook_key: str, *, mode: str) -> str:
    bedtime_goals = {
        "missing_item": "find it without letting bedtime unravel",
        "tiny_creature_problem": "help the tiny visitor and put things right kindly",
        "misunderstanding": "work out what really happened before the mix-up grows",
        "gentle_problem": "restore the calm order of the evening",
        "unexpected_discovery": "understand the clue before it becomes a worry",
    }
    standard_goals = {
        "accidental_mess": "tidy the muddle before it spreads",
        "clever_shortcut": "get everyone back on track with a laugh",
        "helpful_plan_goes_wrong": "fix the plan without blaming anyone",
        "silly_competition": "finish the game in a fair and cheerful way",
        "pretend_game": "turn the pretend trouble into a real solution",
        "misunderstanding": "clear up the mix-up kindly",
        "unexpected_discovery": "follow the clue to a satisfying answer",
        "missing_item": "find the missing thing and finish what they started",
        "gentle_problem": "solve the little problem together",
    }
    goals = bedtime_goals if mode == BEDTIME_MODE else standard_goals
    return goals.get(hook_key, "solve the little problem together")


def _premise_for_hook(
    *,
    hook_key: str,
    mode: str,
    main_characters: list[str],
    supporting_characters: list[str],
    setting: str,
) -> str:
    main_intro = _join_names(main_characters)
    helper = "Buddybug" if "Buddybug" in main_characters + supporting_characters else _join_names(supporting_characters)
    catalyst = "Daphne" if "Daphne" in main_characters + supporting_characters else main_characters[0]
    gentle_friend = "Dolly" if "Dolly" in main_characters + supporting_characters else main_characters[0]

    bedtime_premises = {
        "missing_item": (
            f"In the {setting}, {main_intro} discover that an important bedtime comfort has gone missing. "
            f"With {helper}, they search slowly, follow one useful clue, and put everything right before sleep."
        ),
        "tiny_creature_problem": (
            f"In the {setting}, {main_intro} find a tiny creature beside the wrong thing. "
            f"They help it gently, solve the little problem kindly, and settle the room again."
        ),
        "misunderstanding": (
            f"In the {setting}, {gentle_friend} and {catalyst} read the same clue in two different ways. "
            f"{main_intro} check both guesses, find the real answer, and end the evening feeling safe and calm."
        ),
        "unexpected_discovery": (
            f"In the {setting}, {main_intro} notice a curious clue that was not there before. "
            f"They follow it carefully, uncover a simple answer, and let bedtime become peaceful again."
        ),
        "gentle_problem": (
            f"In the {setting}, {main_intro} notice that one small part of the evening is out of place. "
            f"They work through the muddle together and bring bedtime back into a calm order."
        ),
    }
    standard_premises = {
        "accidental_mess": (
            f"In the {setting}, {main_intro} are trying to finish a simple job when one wobble turns into a funny mess. "
            f"They follow the splashes, fix the real cause, and end up laughing their way through the cleanup."
        ),
        "clever_shortcut": (
            f"In the {setting}, {catalyst} insists on taking a clever shortcut while {main_intro} are meant to be heading somewhere else. "
            f"The shortcut goes wrong in a harmless way, sends them off course, and leaves them laughing as they find the proper path again."
        ),
        "helpful_plan_goes_wrong": (
            f"In the {setting}, {main_intro} start with a sensible plan that should make things easier before story time. "
            f"The plan turns into a bigger muddle than expected, so they have to pause, sort the problem properly, and finish with a cheerful solution."
        ),
        "silly_competition": (
            f"In the {setting}, {main_intro} turn a tiny contest into a funny problem when neither of them wants to give in first. "
            f"The competition gets sillier, a setback forces them to regroup, and the ending stays warm and fair."
        ),
        "pretend_game": (
            f"In the {setting}, {main_intro} get so caught up in a pretend game that it causes a real little problem. "
            f"They rebuild the game properly and keep all the fun."
        ),
        "misunderstanding": (
            f"In the {setting}, {gentle_friend} and {catalyst} make different guesses about the same clue. "
            f"The mix-up sends everyone the wrong way for a moment before the answer makes them laugh."
        ),
        "unexpected_discovery": (
            f"In the {setting}, {main_intro} spot an odd clue and cannot resist following it. "
            f"What starts as a small mystery leads to a playful, satisfying answer."
        ),
        "missing_item": (
            f"In the {setting}, {main_intro} realise that an important thing has disappeared at exactly the wrong moment. "
            f"They track it down through a lively little muddle and finish relieved and pleased."
        ),
    }
    premises = bedtime_premises if mode == BEDTIME_MODE else standard_premises
    return premises.get(
        hook_key,
        f"In the {setting}, {main_intro} face a small child-friendly problem, solve it step by step, and end the story warmly.",
    )


def _generate_title(*, hook_key: str, main_characters: list[str], setting: str, theme: str, mode: str) -> str:
    primary = main_characters[0]
    secondary = main_characters[1] if len(main_characters) > 1 else primary
    theme_title = theme.title()
    if hook_key == "missing_item":
        return f"{primary} and {secondary}'s Missing Surprise"
    if hook_key == "clever_shortcut":
        return f"{primary} and the Clever Shortcut"
    if hook_key == "accidental_mess":
        return f"{primary}, {secondary}, and the Funny Muddle"
    if hook_key == "tiny_creature_problem":
        return f"{primary} and the Tiny Visitor"
    if hook_key == "misunderstanding":
        return f"{primary} and {secondary}'s Mixed-Up Clue"
    if hook_key == "helpful_plan_goes_wrong":
        return f"The {theme_title} Plan for {primary}"
    if hook_key == "silly_competition":
        return f"{primary} and {secondary}'s Silly Contest"
    if hook_key == "unexpected_discovery":
        return f"{primary} and the Strange Find in the {setting.title()}"
    if hook_key == "pretend_game":
        return f"{primary} and {secondary}'s Pretend-Day Problem"
    return f"{primary} and the Gentle Problem"


def build_story_outline(
    *,
    mode: str,
    hook_key: str,
    setting: str,
    theme: str,
    bedtime_feeling: str,
    main_characters: list[str],
    supporting_characters: list[str],
) -> dict[str, str]:
    primary = main_characters[0]
    main_intro = _join_names(main_characters)
    support_intro = _join_names(supporting_characters) if supporting_characters else "their dependable guide"
    resolver = "Verity" if "Verity" in main_characters + supporting_characters else primary
    catalyst = "Daphne" if "Daphne" in main_characters + supporting_characters else primary
    guide = "Buddybug" if "Buddybug" in main_characters + supporting_characters else support_intro
    gentle_friend = "Dolly" if "Dolly" in main_characters + supporting_characters else primary
    if hook_key == "missing_item":
        opening_beat = f"{main_intro} notice that an important comfort item is missing in the {setting}."
        problem_beat = f"{resolver} keeps everyone calm while {catalyst} checks the wrong place first."
        event_beat = f"{guide} spots a small clue that leads the search toward the right corner of the room."
        resolution_beat = f"{main_intro} find the missing item, smooth the muddle out, and feel better at once."
    elif hook_key == "accidental_mess":
        opening_beat = f"{main_intro} bump a wobbling object in the {setting}, and a harmless mess spreads across the table."
        problem_beat = f"{catalyst} tries to fix everything too quickly while {resolver} keeps the mood light."
        event_beat = f"{guide} helps them follow the splashes until someone notices what caused the whole muddle."
        resolution_beat = f"{main_intro} straighten things properly, wipe the mess away, and end up laughing."
    elif hook_key == "clever_shortcut":
        opening_beat = f"{catalyst} proudly leads {main_intro} off the proper route through the {setting} because the shortcut looks quicker."
        problem_beat = f"The shortcut takes a wrong turn, causes a harmless tumble, and leaves everyone facing the wrong way."
        event_beat = f"{guide} helps them realise they are off course while {resolver} finds the proper path back."
        resolution_beat = f"{main_intro} get back on track and turn the mistake into the funniest part of the day."
    elif hook_key == "tiny_creature_problem":
        opening_beat = f"{main_intro} find a tiny creature beside the wrong object in the {setting}."
        problem_beat = f"The little visitor needs help, and everyone must move gently so it does not feel afraid."
        event_beat = f"{guide} notices where the creature really wants to go and helps the group make a safe path."
        resolution_beat = f"{main_intro} help the tiny creature, tidy the space, and feel proud of their kindness."
    elif hook_key == "misunderstanding":
        opening_beat = f"{gentle_friend} and {catalyst} make different guesses about the same clue in the {setting}."
        problem_beat = f"{resolver} listens to both sides while the wrong guesses send the group in two directions."
        event_beat = f"{guide} helps everyone compare what they noticed until the clue finally makes sense."
        resolution_beat = f"{main_intro} understand the mix-up, laugh softly, and settle the problem kindly."
    elif hook_key == "helpful_plan_goes_wrong":
        opening_beat = f"{main_intro} start a helpful plan in the {setting} so they can get ready for the next part of the day."
        problem_beat = f"{catalyst} rushes the job, the pile turns wobbly, and the muddle grows before it gets smaller."
        event_beat = f"{resolver} stops everyone at the right moment while {guide} helps rescue the slipping piece and sort things properly."
        resolution_beat = f"{main_intro} restart the plan properly and finish the job with cheerful relief."
    elif hook_key == "silly_competition":
        opening_beat = f"{main_intro} turn a tiny contest in the {setting} into a lively game when they should really be moving on."
        problem_beat = f"The contest becomes wobblier and sillier than anyone expected, and one wrong move creates a funny setback."
        event_beat = f"{guide} changes the rules at just the right moment, making the whole thing funnier, kinder, and easier to finish."
        resolution_beat = f"{main_intro} end the contest fairly and feel pleased that they enjoyed it together."
    elif hook_key == "pretend_game":
        opening_beat = f"{main_intro} get deeply absorbed in a pretend game in the {setting}."
        problem_beat = f"One make-believe rule causes a real little problem."
        event_beat = f"{guide} notices the useful clue that helps the game become sturdier instead of wobblier."
        resolution_beat = f"{main_intro} rebuild the game properly and keep all the fun."
    elif hook_key == "unexpected_discovery":
        opening_beat = f"{main_intro} spot an odd clue in the {setting} that was not there before."
        problem_beat = f"The clue is puzzling enough to stop everyone in their tracks."
        event_beat = f"{guide} leads a careful search while {resolver} keeps everyone focused on one clue at a time."
        resolution_beat = f"{main_intro} uncover a simple answer that makes the strange clue feel friendly instead of worrying."
    else:
        opening_beat = f"{main_intro} notice that something in the {setting} is quietly out of place."
        problem_beat = f"{resolver} keeps the little problem from turning into a bigger one."
        event_beat = f"{guide} helps the group follow one useful clue at a time."
        resolution_beat = f"{main_intro} solve the problem together and put everything back where it belongs."

    ending_tone = (
        "quiet, warm, cozy, and ready for rest"
        if mode == BEDTIME_MODE
        else "cheerful, playful, tidy, and satisfied"
    )
    return {
        "opening_beat": opening_beat,
        "problem_beat": problem_beat,
        "event_beat": event_beat,
        "resolution_beat": resolution_beat,
        "ending_tone": ending_tone,
    }


def _build_illustration_beats(
    *,
    hook_key: str,
    setting: str,
    main_characters: list[str],
    supporting_characters: list[str],
    opening_beat: str,
    problem_beat: str,
    event_beat: str,
    resolution_beat: str,
    ending_tone: str,
) -> list[StoryBeat]:
    all_characters = ", ".join(main_characters + supporting_characters)
    return [
        StoryBeat(key="opening", label="Opening Hook", text=f"{all_characters} in {setting}: {opening_beat}"),
        StoryBeat(key="problem", label="Problem Beat", text=f"{problem_beat}"),
        StoryBeat(key="event", label="Middle Event", text=f"{event_beat}"),
        StoryBeat(key="resolution", label="Resolution", text=f"{resolution_beat}"),
        StoryBeat(key="ending", label="Ending Tone", text=f"The final image should feel {ending_tone}."),
    ]


def build_story_prompt(plan: StoryPlan) -> str:
    return "\n".join(
        [
            f"Mode: {plan.mode}",
            f"Target tone: {plan.prompt_context.target_tone}",
            f"Target pacing: {plan.prompt_context.target_pacing}",
            f"Hook: {plan.hook_key} - {plan.hook_description}",
            f"Setting: {plan.setting}",
            f"Characters: {', '.join(plan.main_characters + plan.supporting_characters)}",
            f"Opening beat: {plan.opening_beat}",
            f"Problem beat: {plan.problem_beat}",
            f"Event beat: {plan.event_beat}",
            f"Resolution beat: {plan.resolution_beat}",
            f"Ending tone: {plan.ending_tone}",
            f"Hook-first rule: {plan.prompt_context.hook_first_instruction}",
            f"Anti-poetic-overload rule: {plan.prompt_context.anti_poetic_overload_instruction}",
            f"Structure rule: {plan.prompt_context.structure_instruction}",
            f"Guidance: {plan.prompt_context.guidance}",
        ]
    )


def build_story_plan(
    *,
    age_band: str,
    content_lane_key: str | None,
    bedtime_only: bool,
    tone: str | None,
    available_characters: list[str] | None = None,
    include_characters: list[str] | None = None,
    index: int = 0,
    title: str | None = None,
    setting: str | None = None,
    theme: str | None = None,
    bedtime_feeling: str | None = None,
    main_characters: list[str] | None = None,
    supporting_characters: list[str] | None = None,
) -> StoryPlan:
    lane_key = resolve_content_lane_key(age_band, content_lane_key)
    mode = _infer_mode(age_band=age_band, content_lane_key=lane_key, bedtime_only=bedtime_only, tone=tone)
    if main_characters is None or supporting_characters is None:
        chosen_main, chosen_supporting = choose_story_characters(
            available_characters=available_characters or CANONICAL_CHARACTER_ORDER,
            include_characters=include_characters,
            mode=mode,
            index=index,
        )
        main_characters = main_characters or chosen_main
        supporting_characters = supporting_characters or chosen_supporting
    resolved_setting = choose_story_setting(mode=mode, lane_key=lane_key, index=index, explicit_setting=setting)
    resolved_theme = _choose_story_theme(mode=mode, lane_key=lane_key, index=index, explicit_theme=theme)
    resolved_feeling = _choose_story_feeling(
        mode=mode,
        lane_key=lane_key,
        index=index,
        explicit_feeling=bedtime_feeling,
    )
    hook_key = choose_story_hook(
        mode=mode,
        main_characters=main_characters,
        supporting_characters=supporting_characters,
        theme=resolved_theme,
        index=index,
    )
    hook = HOOK_DEFINITIONS[hook_key]
    outline = build_story_outline(
        mode=mode,
        hook_key=hook_key,
        setting=resolved_setting,
        theme=resolved_theme,
        bedtime_feeling=resolved_feeling,
        main_characters=main_characters,
        supporting_characters=supporting_characters,
    )
    prompt_context = StoryPromptContext(
        mode=mode,
        target_tone=tone or _default_tone_for_mode(mode, lane_key),
        target_pacing="engaging, clear, and gently winding down by the end" if mode == BEDTIME_MODE else "playful, witty, and clearly paced",
        hook_first_instruction="The first 2-4 lines must contain a concrete hook that makes the child want to know what happens next.",
        anti_poetic_overload_instruction=(
            "Avoid excessive poetic imagery. Reduce overuse of moonlight, glowing stars, whispering breezes, silver light, and dreamy filler. "
            "Prioritize concrete events, dialogue, and child-friendly plot progression."
        ),
        structure_instruction="Build a clear beginning-middle-end with an opening hook, a small problem, a meaningful middle event, and a satisfying resolution.",
        guidance=(
            "Write a plot-led bedtime story with a clear hook in the opening, a small central problem, at least one playful or surprising middle beat, and a calm sleepy resolution. "
            "Keep the language warm and simple. Avoid excessive poetic imagery or dreamy filler. The story should feel engaging on the way through, then gently settle into a reassuring bedtime ending."
            if mode == BEDTIME_MODE
            else "Write a warm, playful children's story with a clear hook, a small funny problem or mischievous moment, and a satisfying resolution. "
            "Allow cheeky fun and light humour, but keep it kind, safe, and age-appropriate. "
            "Do not drift into bedtime framing: no settling into bed, no falling asleep, and no sleepy goodnight ending unless the lane is explicitly bedtime. "
            "Finish with warm energy, wit, and proud relief rather than drowsiness. It should feel like an engaging afternoon read."
        ),
    )
    resolved_title = title or _generate_title(
        hook_key=hook_key,
        main_characters=main_characters,
        setting=resolved_setting,
        theme=resolved_theme,
        mode=mode,
    )
    illustration_beats = _build_illustration_beats(
        hook_key=hook_key,
        setting=resolved_setting,
        main_characters=main_characters,
        supporting_characters=supporting_characters,
        opening_beat=outline["opening_beat"],
        problem_beat=outline["problem_beat"],
        event_beat=outline["event_beat"],
        resolution_beat=outline["resolution_beat"],
        ending_tone=outline["ending_tone"],
    )
    main_intro = _join_names(main_characters)
    premise = _premise_for_hook(
        hook_key=hook_key,
        mode=mode,
        main_characters=main_characters,
        supporting_characters=supporting_characters,
        setting=resolved_setting,
    )
    return StoryPlan(
        mode=mode,
        title=resolved_title,
        premise=premise,
        hook_key=hook.key,
        hook_description=hook.description,
        setting=resolved_setting,
        theme=resolved_theme,
        bedtime_feeling=resolved_feeling,
        main_characters=main_characters,
        supporting_characters=supporting_characters,
        opening_beat=outline["opening_beat"],
        problem_beat=outline["problem_beat"],
        event_beat=outline["event_beat"],
        resolution_beat=outline["resolution_beat"],
        ending_tone=outline["ending_tone"],
        playful_tone=mode == STANDARD_MODE and lane_key != STORY_ADVENTURES_8_12_LANE_KEY,
        bedtime_suitability=mode == BEDTIME_MODE,
        illustration_beats=illustration_beats,
        prompt_context=prompt_context,
    )


def build_story_plan_from_idea(idea: StoryIdea) -> StoryPlan:
    return build_story_plan(
        age_band=idea.age_band,
        content_lane_key=idea.content_lane_key,
        bedtime_only="playful" not in (idea.tone or "").lower() and "cheeky" not in (idea.tone or "").lower(),
        tone=idea.tone,
        title=idea.title,
        setting=idea.setting,
        theme=idea.theme,
        bedtime_feeling=idea.bedtime_feeling,
        main_characters=_split_names(idea.main_characters),
        supporting_characters=_split_names(idea.supporting_characters),
    )


def estimated_minutes_for_mode(*, mode: str, lane_key: str, index: int = 0) -> int:
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return ADVENTURE_MINUTES[index % len(ADVENTURE_MINUTES)]
    if mode == BEDTIME_MODE:
        return BEDTIME_MINUTES[index % len(BEDTIME_MINUTES)]
    return STANDARD_3_7_MINUTES[index % len(STANDARD_3_7_MINUTES)]
