from __future__ import annotations

from app.models import StoryIdea
from app.schemas.story_pipeline_schema import IllustrationScene, StoryBeatCard, StoryBrief, StoryMetadata, StoryOutline
from app.services.story_engine_data import (
    BEDTIME_MODE,
    DEFAULT_ADVENTURE_TONE,
    STANDARD_MODE,
)
from app.utils.seed_content_lanes import STORY_ADVENTURES_8_12_LANE_KEY


def _split_names(raw_names: str | None) -> list[str]:
    if not raw_names:
        return []
    return [name.strip() for name in raw_names.split(",") if name.strip()]


STORYLIGHT_GUARDIANS = {"Buddybug", "Glowmoth", "Twinklet", "Whisperwing"}


def _infer_mode(idea: StoryIdea) -> str:
    if idea.content_lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return STANDARD_MODE
    normalized_tone = (idea.tone or "").casefold()
    if any(token in normalized_tone for token in {"playful", "cheeky", "mischief", "fun", "humour", "humor", "adventurous"}):
        return STANDARD_MODE
    return BEDTIME_MODE


def _lead_names(idea: StoryIdea) -> tuple[list[str], list[str], str, str]:
    main_characters = _split_names(idea.main_characters)
    supporting_characters = _split_names(idea.supporting_characters)
    lead = main_characters[0] if main_characters else "Buddybug"
    second = main_characters[1] if len(main_characters) > 1 else lead
    return main_characters, supporting_characters, lead, second


def _missing_item_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "bedroom" in lowered:
        return "her patchwork blanket"
    if "garden" in lowered:
        return "the lantern ribbon"
    if "hallway" in lowered:
        return "the bedtime songbook"
    return "the comfort pillow"


def _missing_item_for_idea(idea: StoryIdea) -> str:
    source_text = " ".join(
        part for part in (idea.title, idea.premise, idea.theme, idea.setting) if part
    ).casefold()
    if "songbook" in source_text or "song book" in source_text or "bedtime song" in source_text:
        return "the bedtime songbook"
    if "blanket" in source_text or "quilt" in source_text:
        return "her patchwork blanket"
    if "ribbon" in source_text or "lantern ribbon" in source_text:
        return "the lantern ribbon"
    if "pillow" in source_text or "cushion" in source_text:
        return "the comfort pillow"
    return _missing_item_for_setting(idea.setting)


def _missing_item_clue(*, item: str, setting: str) -> str:
    lowered_item = item.casefold()
    if "songbook" in lowered_item:
        return "a paper corner peeking out beside the rocking chair"
    if "blanket" in lowered_item:
        return "a loose thread caught near the rocking chair"
    if "ribbon" in lowered_item:
        return "a little loop of ribbon caught by the path"
    return _clue_for_setting(setting)


def _missing_item_resolution(*, item: str, lead: str, resolver: str, setting: str) -> str:
    lowered_item = item.casefold()
    if "songbook" in lowered_item:
        return (
            f"{resolver} helped {lead} lift the songbook from where it had slipped, "
            f"set it back by the rocking chair, and straighten the bedtime things."
        )
    if "blanket" in lowered_item:
        return f"{resolver} helped {lead} pull the blanket free, smooth it flat, and put the room back in order."
    if "ribbon" in lowered_item:
        return f"{resolver} helped {lead} free the ribbon, tie it neatly again, and set everything right."
    return f"{resolver} helped {lead} find the missing thing, put it back in its proper place, and put the room back in order."


def _creature_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "garden" in lowered or "meadow" in lowered:
        return "a tiny frog"
    if "bedroom" in lowered:
        return "a fluttery moth"
    return "a little field mouse"


def _mess_for_setting(setting: str) -> tuple[str, str]:
    lowered = setting.casefold()
    if "kitchen" in lowered:
        return "a bowl of blueberry batter", "wooden spoon"
    if "picnic" in lowered or "puddle" in lowered:
        return "a picnic basket", "checked picnic cloth"
    return "a stack of teacups", "tray"


def _clue_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "bedroom" in lowered:
        return "a loose thread caught near the rocking chair"
    if "garden" in lowered or "path" in lowered:
        return "odd little marks by the path"
    if "reading nook" in lowered:
        return "a folded note tucked into the wrong book"
    return "a curious clue in the wrong place"


def _plan_task_for_setting(setting: str) -> tuple[str, str]:
    lowered = setting.casefold()
    if "reading nook" in lowered:
        return "tidy the books before story time", "the pile of books"
    if "toy cupboard" in lowered:
        return "put the toys back quickly", "the stack of boxes"
    if "kitchen" in lowered:
        return "put away the cups and napkins", "the little pile"
    return "tidy everything up", "the growing pile"


def _competition_for_setting(setting: str) -> str:
    lowered = setting.casefold()
    if "puddle" in lowered or "picnic" in lowered or "garden" in lowered or "path" in lowered:
        return "who could hop over the biggest puddle"
    return "who could carry the most things at once"


def _resolver_name(*, lead: str, second: str, calmer: str, helper: str) -> str:
    for candidate in (calmer, second, helper):
        if candidate and candidate != lead:
            return candidate
    return second if second else lead


def _all_characters(idea: StoryIdea) -> list[str]:
    main_characters, supporting_characters, _, _ = _lead_names(idea)
    seen: set[str] = set()
    ordered: list[str] = []
    for name in [*main_characters, *supporting_characters]:
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _scene_must_show_for_hook(idea: StoryIdea) -> dict[str, list[str]]:
    hook_type = idea.hook_type or "gentle_problem"
    setting = idea.setting
    if hook_type == "missing_item":
        item = _missing_item_for_idea(idea)
        clue = _missing_item_clue(item=item, setting=setting)
        return {
            "scene_1": [f"the place where {item} should normally be", setting],
            "scene_2": [item, "concerned but gentle search"],
            "scene_3": [clue, "the place nobody checked properly"],
            "scene_4": [item, "the item being recovered and smoothed back into place"],
            "scene_5": [item, "everyone settled and reassured"],
        }
    if hook_type == "accidental_mess":
        messy_object, extra_item = _mess_for_setting(setting)
        return {
            "scene_1": [messy_object, extra_item, setting],
            "scene_2": ["the wobble or slip beginning", "spilled ingredients or mess"],
            "scene_3": ["the funniest part of the muddle", "a clear cause-and-effect action beat"],
            "scene_4": ["clean-up action", "the problem being put right"],
            "scene_5": ["a tidier room", "warm relief after the muddle"],
        }
    if hook_type == "clever_shortcut":
        return {
            "scene_1": [setting, "the tempting shortcut"],
            "scene_2": ["the wrong turn", "harmless leafy or muddy muddle"],
            "scene_3": ["the funniest tumble or slip"],
            "scene_4": ["the proper path being shown"],
            "scene_5": ["everyone back on track and laughing"],
        }
    if hook_type == "helpful_plan_goes_wrong":
        task, pile_name = _plan_task_for_setting(setting)
        return {
            "scene_1": [task, pile_name],
            "scene_2": [pile_name, "the wobble or over-stacking problem"],
            "scene_3": ["the leaning pile", "a gentle rescue attempt"],
            "scene_4": ["the problem split into smaller neat jobs"],
            "scene_5": ["a tidy room and pleased expressions"],
        }
    return {
        "scene_1": [setting],
        "scene_2": ["the central problem"],
        "scene_3": ["the clearest story action"],
        "scene_4": ["the problem being solved"],
        "scene_5": ["a warm settled ending"],
    }


def _scene_focus_characters(idea: StoryIdea, *, scene_key: str) -> list[str]:
    characters = _all_characters(idea)
    if not characters:
        return []
    if scene_key == "scene_5":
        return characters[:3]
    if scene_key == "scene_3":
        playful = [name for name in characters if name not in {"Verity"}]
        return (playful or characters)[:3]
    return characters[:2] if len(characters) >= 2 else characters[:1]


def _scene_emotion(idea: StoryIdea, *, scene_key: str) -> str:
    mode = _infer_mode(idea)
    if scene_key == "scene_1":
        return "calm curiosity" if mode == BEDTIME_MODE else "playful anticipation"
    if scene_key == "scene_2":
        return "gentle concern" if mode == BEDTIME_MODE else "cheeky problem energy"
    if scene_key == "scene_3":
        return "focused discovery" if mode == BEDTIME_MODE else "playful giggle moment"
    if scene_key == "scene_4":
        return "relief and teamwork"
    return "sleepy reassurance" if mode == BEDTIME_MODE else "warm satisfaction"


def _scene_continuity_notes(idea: StoryIdea, *, scene_key: str) -> list[str]:
    notes = [
        "Keep character design, collar colours, and scale relationships consistent with earlier pages.",
        "Match the page beside the illustration rather than summarising the whole story.",
        "Show a specific visible action, not only a decorative mood scene.",
    ]
    if scene_key in {"scene_4", "scene_5"}:
        notes.append("Carry forward the same props or mess from the previous scene so the resolution feels connected.")
    if any(name in STORYLIGHT_GUARDIANS for name in _all_characters(idea)):
        notes.append("If a guardian is present, keep them small and glowing rather than letting them dominate the composition.")
    return notes


def _scene_must_not_show(idea: StoryIdea) -> list[str]:
    items = [
        "no text labels or captions inside the art",
        "no photorealistic rendering",
        "no extra unrelated characters",
    ]
    all_characters = _all_characters(idea)
    if "Dolly" in all_characters:
        items.append("do not depict Dolly as any species other than a grey dachshund with a blue collar")
    if "Daphne" in all_characters:
        items.append("do not depict Daphne as any species other than a black-and-tan dachshund with a red collar and gold star tag")
    if "Verity" in all_characters:
        items.append("do not depict Verity as a child")
    return items


def build_story_outline(idea: StoryIdea) -> StoryOutline:
    """Convert a short Buddybug idea into a clear opening/problem/event/resolution/ending outline."""
    main_characters, supporting_characters, lead, second = _lead_names(idea)
    helper = supporting_characters[0] if supporting_characters else ("Buddybug" if lead != "Buddybug" else second)
    calmer = "Verity" if "Verity" in main_characters + supporting_characters else second
    hook_type = idea.hook_type or "gentle_problem"
    setting = idea.setting
    mode = _infer_mode(idea)

    if hook_type == "missing_item":
        item = _missing_item_for_idea(idea)
        resolver = _resolver_name(lead=lead, second=second, calmer=calmer, helper=helper)
        opening_hook = f"Just before bed, {lead} discovered that {item} was missing from the {setting}."
        problem = f"Without it, bedtime could not feel quite right, and {second} knew they had to find it quickly but calmly."
        event = (
            f"{helper} spotted {_missing_item_clue(item=item, setting=setting)}, "
            f"and the clue led everyone to the place nobody had checked properly."
        )
        resolution = _missing_item_resolution(item=item, lead=lead, resolver=resolver, setting=setting)
        gentle_ending = f"Everyone settled down feeling {idea.bedtime_feeling}, and the little mystery became the last quiet story of the day."
    elif hook_type == "clever_shortcut":
        opening_hook = f"{lead} announced that there was a quicker way through the {setting}, even though everyone was supposed to stay on the proper path."
        problem = f"The shortcut looked clever at first, but it sent {lead} and {second} the wrong way and left them in a harmless muddle."
        event = f"A sudden slip sent them into a leafy tumble, and even {helper} looked startled before bursting into giggles."
        resolution = f"{calmer} pointed out the real path, and {lead} admitted that the short way is not shorter if you have to do it twice."
        gentle_ending = f"They reached the right place still laughing, a little rumpled, and very {idea.bedtime_feeling}."
    elif hook_type == "accidental_mess":
        messy_object, extra_item = _mess_for_setting(setting)
        if "kitchen" in setting.casefold():
            opening_hook = (
                f"In Verity's household, the first job of the day was making blueberry muffins for tea, "
                f"and {lead} and {second} were hard at work in the {setting} with {messy_object} and the {extra_item}."
            )
            problem = (
                f"Flour drifted, blueberries rolled, and in all the hullabaloo the bowl began to wobble until buttery paws and a quick grab sent it crashing to the floor."
            )
            event = (
                f"When the bowl landed upside down and the batter splashed everywhere, {lead} thought the worst was over until {second} vanished and a muffled bark started tapping from under the bowl."
            )
            resolution = (
                f"{lead} tipped the bowl up with the {extra_item}, helped {second} wriggle free, and {calmer} later helped them clean up and start the muffins properly again."
            )
            gentle_ending = (
                f"By the time the mixing began again, everyone was smiling about blueberry batter, cheeky little secrets, and the funniest baking muddle of the morning."
            )
        else:
            opening_hook = f"In the {setting}, {lead} noticed {messy_object} wobbling far too close to the edge just as {second} reached for the {extra_item}."
            problem = f"One quick bump sent the bowl tipping, and batter slithered across the table before anyone could catch it."
            event = f"{lead} grabbed for the bowl, {second} grabbed for the spoon, and the batter splashed onto sleeves, noses, and the tablecloth in one silly swoop."
            resolution = f"{calmer} stood the bowl upright, straightened the cloth, and helped everyone wipe up the biggest splashes first."
            gentle_ending = f"By the end, the {setting} was tidy again, and everyone was still giggling about the blue spots on their noses."
    elif hook_type == "tiny_creature_problem":
        creature = _creature_for_setting(setting)
        opening_hook = f"In the {setting}, {lead} found {creature} beside something it clearly was not meant to have."
        problem = f"The little visitor needed help, but nobody wanted to frighten it or make the situation worse."
        event = f"{helper} noticed where the creature kept trying to go, and that gave {lead} and {second} the clue they needed."
        resolution = f"{calmer} helped everyone make a safe path, and the tiny problem was solved with gentle hands and patient steps."
        gentle_ending = f"Once the creature was safe again, the whole room felt calmer, kinder, and ready to settle."
    elif hook_type == "misunderstanding":
        clue = _clue_for_setting(setting)
        opening_hook = f"{lead} and {second} both noticed {clue}, and each of them decided they knew exactly what it meant."
        problem = f"Their different guesses sent everyone in two directions, and the small confusion grew before anyone stopped to compare notes."
        event = f"{helper} asked what each of them had actually seen, and suddenly the mixed-up clue started to make sense."
        resolution = f"{calmer} helped put both half-answers together, and the real explanation turned out to be simple and satisfying."
        gentle_ending = f"They laughed softly at the muddle, finished what they had started, and ended the moment feeling {idea.bedtime_feeling}."
    elif hook_type == "helpful_plan_goes_wrong":
        task, pile_name = _plan_task_for_setting(setting)
        opening_hook = f"{lead} decided to help by trying to {task}, and at first the plan looked like an excellent one."
        problem = f"Then {pile_name} grew taller, wobblier, and far harder to manage than anyone had expected."
        event = f"When one piece slipped sideways, {helper} rushed in to help, but that only made the whole muddle lean farther."
        resolution = f"{calmer} slowed everyone down, rescued the slipping piece, and turned one big problem into two small neat jobs."
        gentle_ending = f"Once the job was done, the room felt ready again, and {lead} had a new story to laugh about."
    elif hook_type == "silly_competition":
        competition = _competition_for_setting(setting)
        if "puddle" in competition:
            opening_hook = (
                f"While they were out for a walk after the rain, {lead} and {second} got distracted by an argument about {competition}."
            )
            problem = (
                f"The little contest turned slippery and silly almost at once, and soon nobody could tell whether they were still competing or just splashing."
            )
            event = (
                f"One bold hop ended in a trip, a tumble, and a very splashy landing that sent muddy water in every direction."
            )
            resolution = (
                f"{calmer} declared it a shared win, marched everyone home, and turned the soggy muddle into a warm funny memory."
            )
            gentle_ending = (
                f"Wrapped in towels and feeling {idea.bedtime_feeling}, they kept giggling about the loudest splosh and the silliest jump."
            )
        else:
            opening_hook = f"{lead} and {second} got distracted by an argument about {competition} when they were meant to be doing something else."
            problem = f"The tiny contest quickly became wobblier and sillier than either of them had planned."
            event = f"One wrong move turned the contest into a harmless muddle and a fit of giggles."
            resolution = f"{helper} changed the rules, {calmer} called it a shared win, and the competition ended much more kindly than it began."
            gentle_ending = f"They walked away rosy-cheeked and {idea.bedtime_feeling}, still talking about the funniest moment."
    elif hook_type == "unexpected_discovery":
        clue = _clue_for_setting(setting)
        opening_hook = f"{lead} noticed {clue} in the {setting}, even though it had definitely not been there before."
        problem = f"The strange clue made everyone curious, and they had to decide whether it meant trouble, a mistake, or a surprise."
        event = f"{helper} followed the trail carefully while {second} checked the places that seemed most likely to hold the answer."
        resolution = f"{calmer} helped everyone piece the clue together, and the real answer turned out to be friendly rather than worrying."
        gentle_ending = f"What had seemed odd at first ended as a warm little discovery that left everyone feeling {idea.bedtime_feeling}."
    elif hook_type == "pretend_game":
        opening_hook = f"{lead} and {second} were so deep in a pretend game in the {setting} that the make-believe rules started causing real trouble."
        problem = f"Each of them wanted the game to work their own way, and soon the pretend problem became a real one."
        event = f"{helper} noticed the one useful thing hidden inside the game, and that clue gave everyone a better plan."
        resolution = f"{calmer} helped rebuild the game so it could stay fun without falling into another muddle."
        gentle_ending = f"The story ended with a sturdier game, lighter feelings, and a very pleased pair of players."
    else:
        opening_hook = f"In the {setting}, {lead} noticed that one small part of the day was not quite right."
        problem = f"It was not a big problem, but it was enough to make everyone pause and decide to sort it out."
        event = f"{helper} spotted the clue that showed where to begin, and once they had that, the muddle felt much smaller."
        resolution = f"{calmer} helped {lead} and {second} fix the problem one step at a time."
        gentle_ending = (
            f"The day carried on in a much better way, and the whole group ended feeling {idea.bedtime_feeling}."
            if mode == STANDARD_MODE
            else f"With everything back in place, the evening felt safe, settled, and ready for rest."
        )
    return StoryOutline(
        opening_hook=opening_hook,
        problem=problem,
        event=event,
        resolution=resolution,
        gentle_ending=gentle_ending,
    )


def build_illustration_scenes(idea: StoryIdea, outline: StoryOutline) -> list[IllustrationScene]:
    """Turn the outline into scene-ready illustration prompts."""
    must_show_by_scene = _scene_must_show_for_hook(idea)
    return [
        IllustrationScene(
            key="scene_1",
            label="Opening Hook",
            text=outline.opening_hook,
            focus_characters=_scene_focus_characters(idea, scene_key="scene_1"),
            location_hint=idea.setting,
            action=outline.opening_hook,
            emotion=_scene_emotion(idea, scene_key="scene_1"),
            must_show=must_show_by_scene.get("scene_1", []),
            must_not_show=_scene_must_not_show(idea),
            continuity_notes=_scene_continuity_notes(idea, scene_key="scene_1"),
        ),
        IllustrationScene(
            key="scene_2",
            label="Problem",
            text=outline.problem,
            focus_characters=_scene_focus_characters(idea, scene_key="scene_2"),
            location_hint=idea.setting,
            action=outline.problem,
            emotion=_scene_emotion(idea, scene_key="scene_2"),
            must_show=must_show_by_scene.get("scene_2", []),
            must_not_show=_scene_must_not_show(idea),
            continuity_notes=_scene_continuity_notes(idea, scene_key="scene_2"),
        ),
        IllustrationScene(
            key="scene_3",
            label="Event",
            text=outline.event,
            focus_characters=_scene_focus_characters(idea, scene_key="scene_3"),
            location_hint=idea.setting,
            action=outline.event,
            emotion=_scene_emotion(idea, scene_key="scene_3"),
            must_show=must_show_by_scene.get("scene_3", []),
            must_not_show=_scene_must_not_show(idea),
            continuity_notes=_scene_continuity_notes(idea, scene_key="scene_3"),
        ),
        IllustrationScene(
            key="scene_4",
            label="Resolution",
            text=outline.resolution,
            focus_characters=_scene_focus_characters(idea, scene_key="scene_4"),
            location_hint=idea.setting,
            action=outline.resolution,
            emotion=_scene_emotion(idea, scene_key="scene_4"),
            must_show=must_show_by_scene.get("scene_4", []),
            must_not_show=_scene_must_not_show(idea),
            continuity_notes=_scene_continuity_notes(idea, scene_key="scene_4"),
        ),
        IllustrationScene(
            key="scene_5",
            label="Gentle Ending",
            text=outline.gentle_ending,
            focus_characters=_scene_focus_characters(idea, scene_key="scene_5"),
            location_hint=idea.setting,
            action=outline.gentle_ending,
            emotion=_scene_emotion(idea, scene_key="scene_5"),
            must_show=must_show_by_scene.get("scene_5", []),
            must_not_show=_scene_must_not_show(idea),
            continuity_notes=_scene_continuity_notes(idea, scene_key="scene_5"),
        ),
    ]


def build_story_metadata(
    idea: StoryIdea,
    *,
    style_reference_titles: list[str] | None = None,
    style_reference_examples: list[str] | None = None,
) -> StoryMetadata:
    """Build normalized metadata for generation, rewriting, illustration, and review."""
    main_characters, supporting_characters, _, _ = _lead_names(idea)
    mode = _infer_mode(idea)
    tone = idea.tone
    if idea.content_lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        tone = DEFAULT_ADVENTURE_TONE
    return StoryMetadata(
        mode=mode,
        hook_type=idea.hook_type or "gentle_problem",
        series_key=idea.series_key,
        series_title=idea.series_title,
        tone=tone,
        target_age_band=idea.age_band,
        setting=idea.setting,
        theme=idea.theme,
        bedtime_feeling=idea.bedtime_feeling,
        main_characters=main_characters,
        supporting_characters=supporting_characters,
        style_reference_titles=style_reference_titles or [],
        style_reference_examples=style_reference_examples or [],
        constraints=[
            "must contain a hook",
            "must contain a clear problem",
            "must contain a resolution",
            "must contain dialogue",
            "avoid atmospheric openings",
            "avoid excessive poetic language",
            "bedtime stories should feel calm, story-led, and gently satisfying",
            "standard stories should include a visible giggle moment with harmless comedy",
        ],
    )


def _ordinary_world_for_story(idea: StoryIdea) -> str:
    hook_type = idea.hook_type or "gentle_problem"
    main_characters, _, lead, second = _lead_names(idea)
    pair = " and ".join(main_characters[:2]) if len(main_characters) >= 2 else lead
    setting = idea.setting
    if hook_type == "missing_item":
        return f"{pair} are settling into the {setting} and expecting bedtime to begin as usual."
    if hook_type == "accidental_mess" and "kitchen" in setting.casefold():
        return f"{pair} are helping make blueberry muffins for tea in the {setting}."
    if hook_type == "accidental_mess":
        return f"{pair} are trying to finish a small job in the {setting} before the muddle begins."
    if hook_type == "helpful_plan_goes_wrong":
        return f"{lead} wants to be especially helpful to {second} in the {setting}."
    if hook_type == "silly_competition":
        return f"{pair} are meant to be doing something sensible, but their attention drifts in the {setting}."
    if hook_type == "clever_shortcut":
        return f"{pair} are meant to follow the proper route through the {setting}."
    return f"{pair} are in the {setting}, expecting an ordinary part of the day."


def build_story_beat_card(idea: StoryIdea, *, outline: StoryOutline | None = None) -> StoryBeatCard:
    """Convert a lightweight outline into a more concrete narrative beat card."""
    outline = outline or build_story_outline(idea)
    hook_type = idea.hook_type or "gentle_problem"
    ordinary_world = _ordinary_world_for_story(idea)
    comic_or_surprising_reveal = outline.event
    turning_point = outline.resolution
    if hook_type == "accidental_mess" and "kitchen" in idea.setting.casefold():
        comic_or_surprising_reveal = (
            "Dolly has vanished under the upside-down bowl and dashes out covered in blueberry batter with a silly crown on her head."
        )
        turning_point = "Daphne realises the missing batter mystery is really Dolly's cheeky little secret."
    elif hook_type == "helpful_plan_goes_wrong":
        turning_point = "The wobble finally becomes too obvious to ignore, so everyone has to slow down and rethink the plan."
    elif hook_type == "silly_competition":
        turning_point = "The funniest moment is also the point where the contest clearly needs new rules."
    elif hook_type == "clever_shortcut":
        turning_point = "The tumble makes it obvious that the shortcut is only making the journey longer."

    return StoryBeatCard(
        ordinary_world=ordinary_world,
        inciting_moment=outline.opening_hook,
        problem_escalation=outline.problem,
        comic_or_surprising_reveal=comic_or_surprising_reveal,
        turning_point=turning_point,
        resolution_action=outline.resolution,
        final_emotional_beat=outline.gentle_ending,
        illustration_beats=[
            ordinary_world,
            outline.opening_hook,
            comic_or_surprising_reveal,
            outline.resolution,
            outline.gentle_ending,
        ],
    )


def build_story_brief(
    idea: StoryIdea,
    *,
    style_reference_titles: list[str] | None = None,
    style_reference_examples: list[str] | None = None,
) -> StoryBrief:
    """Build the durable narrative brief that future one-pass story generation will use."""
    metadata = build_story_metadata(
        idea,
        style_reference_titles=style_reference_titles,
        style_reference_examples=style_reference_examples,
    )
    outline = build_story_outline(idea)
    beat_card = build_story_beat_card(idea, outline=outline)
    return StoryBrief(
        mode=metadata.mode,
        target_age_band=metadata.target_age_band,
        hook_type=metadata.hook_type,
        tone=metadata.tone,
        theme=metadata.theme,
        setting=metadata.setting,
        bedtime_feeling=metadata.bedtime_feeling,
        humour_level="gentle" if metadata.mode == BEDTIME_MODE else "giggly",
        tension_ceiling="low" if metadata.mode == BEDTIME_MODE else "mild",
        target_word_count=680 if metadata.mode == BEDTIME_MODE else 720,
        main_characters=metadata.main_characters,
        supporting_characters=metadata.supporting_characters,
        series_key=metadata.series_key,
        series_title=metadata.series_title,
        generation_rules=[
            "write a real story, not a writing exercise",
            "keep setup, problem, reveal, and ending in a single coherent line of action",
            "show the physical cause and effect clearly",
            "avoid poetic filler and meta language",
            "use simple natural language for ages 5-7",
            "land the hook in the first two sentences",
            "write in 5 short paragraphs with a clear beginning, middle, and ending",
            "include at least two lines of spoken dialogue using standard double quotes",
            "make the ending explicitly show the problem being found, fixed, solved, or put right",
            "end with a warm, satisfying final beat",
            "for bedtime stories, keep the plot calm but concrete with 2-4 visible middle beats",
            "let bedtime stories move forward through specific gentle actions, not atmosphere alone",
            "when the setting is outdoors or garden-like, prefer one or more child-friendly goodnight encounters with tiny creatures",
            "middle beats should introduce new visible story business such as a clue, creature, object, greeting, or discovery",
            "for adventure and standard stories, include at least one mischievous, giggly, or funny moment that makes children laugh",
            "adventure stories should feel upbeat and engaging, not calm or sleepy",
        ],
        style_reference_titles=metadata.style_reference_titles,
        style_reference_examples=style_reference_examples or [],
        beat_card=beat_card,
    )
