from dataclasses import dataclass
import logging

from sqlmodel import Session

from app.config import (
    STORY_GENERATION_API_KEY,
    STORY_GENERATION_DEBUG,
    STORY_GENERATION_MODEL,
    STORY_GENERATION_REQUIRE_LIVE,
)
from app.models import StoryDraft, StoryIdea
from app.schemas.story_pipeline_schema import (
    IllustrationScene,
    StoryBrief,
    StoryMetadata,
    StoryOutline,
    StoryValidationIssue,
    StoryValidationResult,
)
from app.services.story_generation_service import StoryGenerationCandidate, generate_story_candidates_from_brief
from app.services.story_planner import build_illustration_scenes, build_story_brief, build_story_metadata, build_story_outline
from app.services.story_quality_service import (
    QualityIssueSignal,
    compute_quality_score,
    detect_age_band_mismatch,
    detect_character_identity_issues,
    detect_narrative_coherence,
    detect_story_constraint_issues,
    detect_story_length_issues,
)
from app.services.story_suggestion_service import (
    build_story_suggestion_guidance_lines,
    list_story_suggestion_references,
)
from app.services.story_style_rewriter import rewrite_story_to_buddybug_style
from app.services.style_engine import list_style_reference_examples
from app.utils.seed_content_lanes import STORY_ADVENTURES_8_12_LANE_KEY

logger = logging.getLogger(__name__)

REVIEW_READY_SCORE_THRESHOLD = 82


@dataclass(frozen=True)
class StoryDraftPayload:
    title: str
    content_lane_key: str
    full_text: str
    summary: str
    read_time_minutes: int
    review_status: str
    generation_source: str
    generated_story: str
    rewritten_story: str
    story_brief: StoryBrief
    story_validation: StoryValidationResult
    story_outline: StoryOutline
    illustration_scenes: list[IllustrationScene]
    story_metadata: StoryMetadata


@dataclass(frozen=True)
class StoryCandidateEvaluation:
    candidate: StoryGenerationCandidate
    score: int
    issues: tuple[QualityIssueSignal, ...]
    issue_codes: tuple[str, ...]


def _join_names(names: list[str]) -> str:
    if not names:
        return "their friends"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def _estimate_read_time(full_text: str, *, lane_key: str) -> int:
    word_count = len(full_text.split())
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        return min(12, max(7, round(word_count / 145)))
    return min(8, max(5, round(word_count / 125)))


def _setting_detail(setting: str) -> str:
    lowered = setting.casefold()
    if "reading nook" in lowered:
        return "Soft cushions were waiting by the shelf, and everyone was meant to settle down for a story."
    if "garden" in lowered or "path" in lowered:
        return "The path looked simple enough, with a gate ahead and plenty of room for a sensible walk."
    if "bedroom" in lowered:
        return "The lamp was low, the pillows were ready, and bedtime had nearly begun."
    if "kitchen" in lowered:
        return "The table was busy, and there was just one last little job to finish."
    if "puddle" in lowered:
        return "The grass was damp, the rain had only just stopped, and there was a perfectly splashy puddle nearby."
    if "picnic" in lowered:
        return "The grass was damp, the basket was ready, and there was a perfectly splashy puddle nearby."
    return f"It should have been an ordinary moment in the {setting}."


def _opening_dialogue(metadata: StoryMetadata) -> str:
    lead = metadata.main_characters[0] if metadata.main_characters else "Buddybug"
    if metadata.mode == "bedtime":
        return f'"Where could it have gone?" asked {lead}.'
    if metadata.hook_type == "clever_shortcut":
        return f'"Leave it to me," said {lead}. "I know a much quicker way."'
    if metadata.hook_type == "helpful_plan_goes_wrong":
        return f'"I can do it all at once," said {lead}, sounding very pleased with the idea.'
    if metadata.hook_type == "silly_competition":
        return f'"I bet I can do it better," said {lead}.'
    return f'"I can fix this," said {lead}.'


def _middle_dialogue(metadata: StoryMetadata) -> str:
    if len(metadata.main_characters) > 1:
        speaker = metadata.main_characters[1]
    elif metadata.supporting_characters:
        speaker = metadata.supporting_characters[0]
    else:
        speaker = metadata.main_characters[0] if metadata.main_characters else "Verity"
    if metadata.mode == "bedtime":
        return f'"Slowly now," said {speaker}. "We only need one good clue."'
    return f'"Maybe we should stop rushing," said {speaker}.'


def _ending_dialogue(metadata: StoryMetadata) -> str:
    speaker = "Verity" if "Verity" in metadata.main_characters + metadata.supporting_characters else (
        metadata.supporting_characters[0]
        if metadata.supporting_characters
        else metadata.main_characters[0]
    )
    if metadata.mode == "bedtime":
        return f'"There now," said {speaker}. "Everything is right again."'
    return f'"That was quite a way to solve it," said {speaker}, smiling.'


def _bedtime_creature_lines(metadata: StoryMetadata) -> tuple[str, str]:
    lowered = metadata.setting.casefold()
    if "garden" in lowered or "path" in lowered or "meadow" in lowered:
        return (
            "By the flower border they paused to whisper goodnight to a small hedgehog shuffling home through the leaves.",
            "A shiny worm wriggled across the path, so they stepped carefully around it and wished it goodnight too.",
        )
    if "bedroom" in lowered or "house" in lowered:
        return (
            "At the window they spotted a sleepy moth resting near the glass, and they whispered a quiet goodnight before moving on.",
            "Buddybug's glow helped them notice one tiny beetle making its way along the sill, and that became one more gentle thing to greet.",
        )
    return (
        "They noticed one tiny creature nearby and took a moment to greet it softly before moving on.",
        "That small goodnight moment made the whole bedtime adventure feel more real and more kind.",
    )


def _style_target_word_count(style_examples: list[str], *, mode: str) -> int:
    if style_examples:
        average = round(sum(len(example.split()) for example in style_examples) / len(style_examples))
        return max(600, min(800, average))
    return 680 if mode == "bedtime" else 720


def _build_bedtime_story(
    *,
    outline: StoryOutline,
    metadata: StoryMetadata,
) -> str:
    lead = metadata.main_characters[0] if metadata.main_characters else "Buddybug"
    second = metadata.main_characters[1] if len(metadata.main_characters) > 1 else lead
    helper = metadata.supporting_characters[0] if metadata.supporting_characters else second
    calmer = "Verity" if "Verity" in metadata.main_characters + metadata.supporting_characters else helper

    paragraphs = [
        (
            f"{outline.opening_hook} {_setting_detail(metadata.setting)} "
            f"{_opening_dialogue(metadata)} {second} stopped at once, because the question mattered to both of them. "
            f"It was only a small bedtime problem, but small bedtime problems can feel very important when the room is nearly ready for sleep."
        ),
        (
            f"{outline.problem} {calmer} kept their voice soft and steady. "
            f"{lead} looked in the first likely place. {second} looked in the next. "
            f"{helper} watched the corners and shelves where little clues like to hide. "
            f"{_middle_dialogue(metadata)} {_bedtime_creature_lines(metadata)[0]}"
        ),
        (
            f"They did not rush. They checked one place, then another. "
            f"When the first guess was wrong, they did not worry. They simply tried the next one. "
            f"That way, the room stayed peaceful even while the mystery stayed real. "
            f"With each careful look, the answer came a little closer. {_bedtime_creature_lines(metadata)[1]}"
        ),
        (
            f"{outline.event} The surprise was gentle, but it was enough to make {lead} blink and {second} smile. "
            f"Even in a calm bedtime story, there is room for one warm little moment that feels unexpected and lovely. "
            f"{helper} seemed very pleased to be the one who had noticed it."
        ),
        (
            f"{outline.resolution} Once they understood what had happened, everything else was easy. "
            f"{lead} helped with the first part. {second} helped with the next. "
            f"{calmer} made sure the muddle stayed small and never grew into anything bigger. "
            f"Soon the room felt neat, safe, and ready again."
        ),
        (
            f"{outline.gentle_ending} {_ending_dialogue(metadata)} "
            f"No one hurried after that. The pillows were plumped. The blankets were smoothed. "
            f"Before long, the room felt comfortable, relieved, and quietly satisfied again."
        ),
    ]
    return "\n\n".join(paragraphs)


def _giggle_line(metadata: StoryMetadata) -> str:
    lead = metadata.main_characters[0] if metadata.main_characters else "Buddybug"
    second = metadata.main_characters[1] if len(metadata.main_characters) > 1 else lead
    if metadata.hook_type == "clever_shortcut":
        return f"When {lead} sat up with bits of leaf stuck in their hair and {second} trying not to laugh, the giggle escaped everyone at once."
    if metadata.hook_type == "helpful_plan_goes_wrong":
        return f"The wobble looked so silly that {lead} tried to stay serious for exactly one second before laughing anyway."
    if metadata.hook_type == "accidental_mess":
        return "One look at the splashes on their noses was enough to start a proper fit of giggles."
    if metadata.hook_type == "silly_competition":
        return "The moment one of them landed with a splash, the whole contest turned into a giggle before anyone could stop it."
    return "That was the sort of harmless muddle that makes children giggle before the problem is even fixed."


def _standard_extra_lines(metadata: StoryMetadata) -> list[str]:
    if metadata.hook_type == "silly_competition" and "puddle" in metadata.setting.casefold():
        return [
            "The puddle looked wider every time they stepped back to judge it properly.",
            "Even Verity could see that the contest had become far sillier than sensible.",
            "By then, nobody was dry enough to claim they had stayed dignified.",
            "The wet pawprints on the floor later made the whole adventure funnier still.",
            "A warm towel and a fire sounded better than one more jump.",
            "That only made the giggles come back all over again.",
        ]
    if metadata.hook_type == "accidental_mess" and "kitchen" in metadata.setting.casefold():
        return [
            "Flour kept settling over the table while the blueberries rolled into ridiculous hiding places.",
            "That only made the kitchen look more as though a tiny baking storm had blown through it.",
            "The tapping under the bowl sounded so odd that it took a moment to understand what it could be.",
            "Once Dolly came dashing out, nobody could pretend the muddle was ordinary anymore.",
            "The blueberry blob on top of Dolly's head looked exactly like a silly little crown.",
            "By then, it was obvious that somebody had tasted more batter than they meant to admit.",
        ]
    return [
        "They kept noticing one more silly detail every time they thought the muddle was over.",
        "That only made it harder not to laugh.",
        "Even the biggest part of the muddle felt harmless once everyone stopped rushing.",
        "Soon the whole business felt more funny than troublesome.",
        "Nobody could stay serious for very long after that.",
        "That sort of harmless trouble always seems funnier the second time it is told.",
    ]


def _build_standard_story(
    *,
    outline: StoryOutline,
    metadata: StoryMetadata,
) -> str:
    lead = metadata.main_characters[0] if metadata.main_characters else "Buddybug"
    second = metadata.main_characters[1] if len(metadata.main_characters) > 1 else lead
    helper = metadata.supporting_characters[0] if metadata.supporting_characters else second
    calmer = "Verity" if "Verity" in metadata.main_characters + metadata.supporting_characters else helper

    if metadata.hook_type == "silly_competition" and "puddle" in metadata.setting.casefold():
        paragraphs = [
            (
                f"{outline.opening_hook} {_setting_detail(metadata.setting)} "
                f"{_opening_dialogue(metadata)} {second} could tell at once that this was exactly the kind of idea that might end brilliantly or end in a soggy mess. "
                f"Either way, it was far too exciting to ignore."
            ),
            (
                f"{outline.problem} {lead} took three careful steps back, stared hard at the puddle, and insisted the next hop would be the perfect one. "
                f"{second} tried to show how it should be done. {helper} tried to warn them before the ground grew any muddier. "
                f"\"Maybe we should stop rushing,\" said {second}."
            ),
            (
                f"{outline.event} {lead} went up, came down, and landed upside down in the puddle with a tremendous splosh. "
                f"Water dripped off {lead}'s nose. {second} tried to look concerned and failed at once. "
                f"{helper} darted forward, then stopped with a hand over their mouth because the sight was simply too funny. "
                f"{_giggle_line(metadata)}"
            ),
            (
                f"For one second it looked as though the contest might start all over again. "
                f"But {calmer} was wiser than that. {calmer} changed the rules on the spot and declared that the biggest splash counted as a shared win. "
                f"That settled the matter much faster than another jump would have done."
            ),
            (
                f"{outline.resolution} {lead} helped with the wet boots. {second} fetched the warm towel. "
                f"{helper} made sure no puddle prints spread farther than the door. "
                f"Soon the whole muddle had shrunk into a damp, cheerful memory."
            ),
            (
                f"{outline.gentle_ending} {_ending_dialogue(metadata)} "
                f"By the time everyone was warm again, the loudest splosh had become the best part of the story. "
                f"Every time they remembered {lead} landing upside down, another giggle escaped."
            ),
        ]
    elif metadata.hook_type == "accidental_mess" and "kitchen" in metadata.setting.casefold():
        paragraphs = [
            (
                f"{outline.opening_hook} {_setting_detail(metadata.setting)} "
                f"They weighed the flour, cleaned the blueberries, and tipped everything into the big bowl together. "
                f"It was great fun, even if it was a little messy. Flour floated through the air like pale dust, and runaway blueberries kept rolling off across the floor."
            ),
            (
                f"{outline.problem} {lead} tried to catch the bowl at once, but buttery paws are not much use for gripping. "
                f"The bowl slipped away, hit the floor with a crash, and landed upside down with a loud thump. "
                f"Some batter splashed onto the wall. Some landed on the floor. Some slid under the table before anyone could stop it. "
                f"\"Can you get a cloth, please?\" said {lead}."
            ),
            (
                f"{outline.event} When {lead} looked around for {second}, there was no sign of them at all. "
                f"Then came a faint tapping, followed by a small muffled bark from down by the floor. "
                f"{lead} poked at the upside-down bowl with the wooden spoon, then used it to tip the bowl up. "
                f"{second} dashed out covered in blueberry batter, with a blob on top of their head like a lopsided crown and sticky paws pattering across the floor. "
                f"{_giggle_line(metadata)}"
            ),
            (
                f"{lead} stared at the nearly empty bowl and blinked. "
                f"The bowl had been much fuller a moment ago, and yet {second} suddenly looked very pleased with themselves. "
                f"{lead} asked where all the rest had gone, but {second} only licked a bit of blueberry from their whiskers and looked innocent. "
                f"That made {helper} laugh first and {lead} laugh straight after."
            ),
            (
                f"{outline.resolution} Over the next few minutes, {second} washed the batter out of their fur while {lead} wiped the wall, swept the floor, and put the bowl back on the table. "
                f"By the time {calmer} came into the kitchen, the pair of them were already trying to look as though they had only just started."
            ),
            (
                f"{outline.gentle_ending} {_ending_dialogue(metadata)} "
                f"\"Are the muffins in the oven already?\" asked {calmer}. Both of them shook their heads and reached for the ingredients as quickly as they could. "
                f"{calmer} gave them a knowing look, came over to help, and said the muffins still had time if everyone stopped playing and started baking properly. "
                f"{lead} gave {second} a small scowl, but {second} did not seem troubled at all."
            ),
        ]
    else:
        paragraphs = [
            (
                f"{outline.opening_hook} {_setting_detail(metadata.setting)} "
                f"{_opening_dialogue(metadata)} {second} knew at once that this was exactly the kind of idea that might end brilliantly or end in a heap. "
                f"Either way, it was far too interesting to ignore."
            ),
            (
                f"{outline.problem} {lead} kept going for a moment longer than was wise. "
                f"{second} tried to help. {helper} tried to warn them. "
                f"That only made the whole business wobblier, sillier, and much harder not to watch. "
                f"{_middle_dialogue(metadata)}"
            ),
            (
                f"Then the muddle turned properly funny. "
                f"{outline.event} {lead} made one face. {second} made another. "
                f"{helper} darted about as if trying to decide whether to help first or laugh first. "
                f"{_giggle_line(metadata)}"
            ),
            (
                f"For a moment the muddle looked as though it might get even bigger. "
                f"But {calmer} finally spotted the one sensible thing to do. "
                f"That was a relief, because none of the silly ideas had worked at all. "
                f"Everyone stopped fussing, looked properly, and began fixing the right problem instead of the loudest one."
            ),
            (
                f"{outline.resolution} Once the useful plan was finally the plan everyone followed, the answer came quickly. "
                f"{lead} helped with the awkward part. {second} handled the fiddly bit. {helper} kept watch for anything else that might slip, splash, topple, or tumble. "
                f"The whole muddle shrank until it was only a funny memory with a damp edge or two."
            ),
            (
                f"{outline.gentle_ending} {_ending_dialogue(metadata)} "
                f"After that, every time anyone remembered the funniest moment, another small giggle escaped."
            ),
        ]
    return "\n\n".join(paragraphs)


def _build_first_pass_story(
    *,
    outline: StoryOutline,
    metadata: StoryMetadata,
) -> str:
    if metadata.mode == "bedtime":
        return _build_bedtime_story(outline=outline, metadata=metadata)
    return _build_standard_story(outline=outline, metadata=metadata)


def _expand_to_target_length(text: str, *, target_words: int, mode: str, hook_type: str, setting: str) -> str:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    additions = (
        [
            "They looked under the obvious things first, then under the places people usually forget.",
            "Each small clue helped the answer feel less far away.",
            "What helped most was that everyone stayed gentle, even while the little mystery was unsolved.",
            "Soon they were noticing the sort of tiny details that matter in a bedroom at bedtime.",
            "The room never felt noisy or hurried, only thoughtful and quietly busy.",
            "That made the answer easier to spot when it finally appeared.",
        ]
        if mode == "bedtime"
        else _standard_extra_lines(
            StoryMetadata(
                mode=mode,
                hook_type=hook_type,
                tone="",
                target_age_band="",
                setting=setting,
                theme="",
                bedtime_feeling="",
            )
        )
    )
    index = 0
    while len(" ".join(paragraphs).split()) < target_words and paragraphs:
        paragraph_index = min(len(paragraphs) - 1, 1 + (index % max(len(paragraphs) - 2, 1)))
        paragraphs[paragraph_index] = f"{paragraphs[paragraph_index]} {additions[index % len(additions)]}"
        index += 1
        if index > 24:
            break
    return "\n\n".join(paragraphs)


def _temporary_story_draft_for_text(
    *,
    idea: StoryIdea,
    lane_key: str,
    text: str,
    source: str,
) -> StoryDraft:
    return StoryDraft(
        story_idea_id=idea.id,
        title=idea.title,
        age_band=idea.age_band,
        language="en",
        content_lane_key=lane_key,
        full_text=text,
        summary="",
        read_time_minutes=0,
        review_status="draft_pending_review",
        generation_source=source,
    )


def _candidate_specific_issues(
    *,
    text: str,
    metadata: StoryMetadata,
    story_brief: StoryBrief,
) -> list[QualityIssueSignal]:
    lowered = text.casefold()
    issues: list[QualityIssueSignal] = []
    meta_terms = {
        "the story",
        "writing exercise",
        "hook-first",
        "anti-poetic",
        "resolution beat",
        "ending tone",
        "structure rule",
    }
    if any(term in lowered for term in meta_terms):
        issues.append(
            QualityIssueSignal(
                code="meta_language_leakage",
                message="The story still contains meta writing language instead of natural prose.",
                severity="high",
                deduction=20,
            )
        )
    for name in metadata.main_characters:
        if name.casefold() not in lowered:
            issues.append(
                QualityIssueSignal(
                    code="missing_main_character",
                    message=f"Main character '{name}' is missing from the generated draft.",
                    severity="high",
                    deduction=12,
                )
            )
    if story_brief.mode != "bedtime" and not any(token in lowered for token in {"giggle", "laugh", "laughed", "grin", "splosh", "splash"}):
        issues.append(
            QualityIssueSignal(
                code="missing_playful_payoff",
                message="The playful draft lacks a visible giggle or comedy payoff.",
                severity="medium",
                deduction=10,
            )
        )
    if story_brief.mode == "bedtime" and not any(token in lowered for token in {"quiet", "calm", "soft", "cozy", "sleepy", "gentle"}):
        issues.append(
            QualityIssueSignal(
                code="missing_bedtime_softness",
                message="The bedtime draft lacks enough soft or calming cues.",
                severity="medium",
                deduction=8,
            )
        )
    if story_brief.mode == "bedtime" and not any(
        token in lowered for token in {"hedgehog", "worm", "moth", "beetle", "frog", "firefly", "mouse", "goodnight"}
    ):
        issues.append(
            QualityIssueSignal(
                code="limited_concrete_bedtime_beats",
                message="The bedtime draft feels too atmospheric and would benefit from one or more concrete gentle encounters.",
                severity="medium",
                deduction=8,
            )
        )
    return issues


def _repetition_issues(text: str) -> list[QualityIssueSignal]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    lowered_sentences = []
    for paragraph in paragraphs:
        lowered_sentences.extend(
            sentence.strip().casefold()
            for sentence in paragraph.split(". ")
            if sentence.strip()
        )
    issues: list[QualityIssueSignal] = []
    seen: set[str] = set()
    repeated = {sentence for sentence in lowered_sentences if sentence in seen or seen.add(sentence)}
    repeated = {sentence for sentence in repeated if len(sentence.split()) >= 6}
    if repeated:
        issues.append(
            QualityIssueSignal(
                code="repeated_story_beats",
                message="The candidate repeats one or more sentences or beat explanations.",
                severity="medium",
                deduction=10,
            )
        )
    paragraph_starts = [paragraph.split(".")[0].strip().casefold() for paragraph in paragraphs if paragraph.strip()]
    if len(paragraph_starts) != len(set(paragraph_starts)) and len(paragraph_starts) >= 4:
        issues.append(
            QualityIssueSignal(
                code="repeated_paragraph_setup",
                message="Several paragraphs begin by restating the same beat instead of moving the story forward.",
                severity="medium",
                deduction=8,
            )
        )
    return issues


def _setup_and_ending_issues(
    *,
    text: str,
    story_brief: StoryBrief,
) -> list[QualityIssueSignal]:
    lowered = text.casefold()
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    issues: list[QualityIssueSignal] = []
    if paragraphs:
        first_paragraph = paragraphs[0].casefold()
        if not any(token in first_paragraph for token in {story_brief.setting.casefold(), *[name.casefold() for name in story_brief.main_characters]}):
            issues.append(
                QualityIssueSignal(
                    code="weak_story_setup",
                    message="The opening paragraph does not clearly ground the setting and key characters.",
                    severity="medium",
                    deduction=10,
                )
            )
    if paragraphs:
        last_paragraph = paragraphs[-1].casefold()
        if not any(token in last_paragraph for token in {"smile", "smiled", "quiet", "warm", "giggle", "laughed", "sleep", "calm"}):
            issues.append(
                QualityIssueSignal(
                    code="weak_final_beat",
                    message="The ending lands without a strong warm or satisfying final beat.",
                    severity="medium",
                    deduction=8,
                )
            )
        if story_brief.mode != "bedtime" and any(
            token in last_paragraph for token in {"sleep", "sleepy", "bedtime", "goodnight", "blanket", "pillow", "yawn"}
        ):
            issues.append(
                QualityIssueSignal(
                    code="sleepy_final_beat_for_adventure",
                    message="The ending becomes sleepy or bedtime-coded when the brief calls for a non-bedtime payoff.",
                    severity="medium",
                    deduction=12,
                )
            )
    if story_brief.beat_card.comic_or_surprising_reveal:
        reveal_tokens = {
            token
            for token in story_brief.beat_card.comic_or_surprising_reveal.casefold().replace("-", " ").split()
            if len(token) > 4
        }
        if reveal_tokens and not any(token in lowered for token in list(reveal_tokens)[:4]):
            issues.append(
                QualityIssueSignal(
                    code="missing_key_reveal",
                    message="The story does not clearly realise the planned comic or surprising reveal from the brief.",
                    severity="high",
                    deduction=14,
                )
            )
    return issues


def _to_validation_result(
    evaluation: StoryCandidateEvaluation,
    *,
    candidate_count: int,
) -> StoryValidationResult:
    review_required = (
        evaluation.score < REVIEW_READY_SCORE_THRESHOLD
        or evaluation.candidate.source == "legacy_fallback"
        or any(issue.severity == "high" for issue in evaluation.issues)
    )
    return StoryValidationResult(
        score=evaluation.score,
        review_required=review_required,
        selected_source=evaluation.candidate.source,
        selected_prompt=evaluation.candidate.prompt or None,
        candidate_count=candidate_count,
        used_fallback=evaluation.candidate.source == "legacy_fallback",
        issue_codes=list(evaluation.issue_codes),
        issues=[
            StoryValidationIssue(
                code=issue.code,
                message=issue.message,
                severity=issue.severity,
                deduction=issue.deduction,
            )
            for issue in evaluation.issues
        ],
    )


def _review_status_for_validation(story_validation: StoryValidationResult) -> str:
    return "needs_revision" if story_validation.review_required else "draft_pending_review"


def _evaluate_story_candidate(
    *,
    candidate: StoryGenerationCandidate,
    idea: StoryIdea,
    lane_key: str,
    metadata: StoryMetadata,
    story_brief: StoryBrief,
) -> StoryCandidateEvaluation:
    draft = _temporary_story_draft_for_text(
        idea=idea,
        lane_key=lane_key,
        text=candidate.text,
        source=candidate.source,
    )
    issues = [
        *detect_story_length_issues(draft),
        *detect_age_band_mismatch(draft),
        *detect_narrative_coherence(draft),
        *detect_story_constraint_issues(draft),
                *detect_character_identity_issues(draft),
        *_candidate_specific_issues(text=candidate.text, metadata=metadata, story_brief=story_brief),
        *_repetition_issues(candidate.text),
        *_setup_and_ending_issues(text=candidate.text, story_brief=story_brief),
    ]
    return StoryCandidateEvaluation(
        candidate=candidate,
        score=compute_quality_score(issues=issues),
        issues=tuple(issues),
        issue_codes=tuple(issue.code for issue in issues),
    )


def _select_story_candidate(
    *,
    candidates: list[StoryGenerationCandidate],
    idea: StoryIdea,
    lane_key: str,
    metadata: StoryMetadata,
    story_brief: StoryBrief,
) -> StoryCandidateEvaluation | None:
    if not candidates:
        return None
    evaluations = [
        _evaluate_story_candidate(
            candidate=candidate,
            idea=idea,
            lane_key=lane_key,
            metadata=metadata,
            story_brief=story_brief,
        )
        for candidate in candidates
    ]
    passing = [item for item in evaluations if item.score >= 72]
    ranked = passing or evaluations
    ranked.sort(key=lambda item: (item.score, len(item.issue_codes) * -1), reverse=True)
    return ranked[0]


def generate_story_draft_payload(idea: StoryIdea, *, session: Session | None = None) -> StoryDraftPayload:
    """Generate a review-ready Buddybug draft through a structured multi-stage pipeline.

    Calm bedtime stories should still be real stories, not only atmosphere.
    """
    style_examples = (
        list_style_reference_examples(
            session,
            age_band=idea.age_band,
            content_lane_key=idea.content_lane_key,
            limit=3,
        )
        if session is not None
        else []
    )
    suggestion_guidance = (
        build_story_suggestion_guidance_lines(
            list_story_suggestion_references(
                session,
                age_band=idea.age_band,
                limit=3,
            )
        )
        if session is not None
        else []
    )
    outline = build_story_outline(idea)
    illustration_scenes = build_illustration_scenes(idea, outline)
    metadata = build_story_metadata(
        idea,
        style_reference_titles=[example.title for example in style_examples],
        style_reference_examples=[example.text for example in style_examples],
    )
    story_brief = build_story_brief(
        idea,
        style_reference_titles=[example.title for example in style_examples],
        style_reference_examples=[example.text for example in style_examples],
        editorial_guidance=suggestion_guidance,
    )
    lane_key = idea.content_lane_key or ("story_adventures_3_7" if idea.age_band == "8-12" else "bedtime_3_7")
    live_generation_requested = bool(STORY_GENERATION_API_KEY.strip() and STORY_GENERATION_MODEL.strip())
    legacy_generated_story = _build_first_pass_story(outline=outline, metadata=metadata)
    legacy_generated_story = _expand_to_target_length(
        legacy_generated_story,
        target_words=_style_target_word_count(metadata.style_reference_examples, mode=metadata.mode),
        mode=metadata.mode,
        hook_type=metadata.hook_type,
        setting=metadata.setting,
    )
    legacy_rewritten_story = rewrite_story_to_buddybug_style(
        generated_story=legacy_generated_story,
        outline=outline,
        metadata=metadata,
    )
    model_candidates = generate_story_candidates_from_brief(story_brief)
    if STORY_GENERATION_DEBUG:
        logger.info(
            "Story writer candidate summary: live_requested=%s model_candidates=%s require_live=%s",
            live_generation_requested,
            len(model_candidates),
            STORY_GENERATION_REQUIRE_LIVE,
        )
    fallback_candidate = StoryGenerationCandidate(
        text=legacy_rewritten_story,
        source="legacy_fallback",
        prompt="legacy_structured_writer",
    )
    candidate_pool = model_candidates if (STORY_GENERATION_REQUIRE_LIVE and live_generation_requested) else [*model_candidates, fallback_candidate]
    selected = _select_story_candidate(
        candidates=candidate_pool,
        idea=idea,
        lane_key=lane_key,
        metadata=metadata,
        story_brief=story_brief,
    )
    if selected is None:
        if STORY_GENERATION_REQUIRE_LIVE and live_generation_requested:
            raise RuntimeError("Live story generation produced no usable candidates and fallback is disabled.")
        selected = _evaluate_story_candidate(
            candidate=StoryGenerationCandidate(
                text=legacy_rewritten_story,
                source="legacy_fallback",
                prompt="legacy_structured_writer",
            ),
            idea=idea,
            lane_key=lane_key,
            metadata=metadata,
            story_brief=story_brief,
        )
    story_validation = _to_validation_result(selected, candidate_count=len(candidate_pool))
    if STORY_GENERATION_REQUIRE_LIVE and live_generation_requested and selected.candidate.source == "legacy_fallback":
        raise RuntimeError("Live story generation fell back to the legacy writer while STORY_GENERATION_REQUIRE_LIVE is enabled.")
    if STORY_GENERATION_DEBUG:
        logger.info(
            "Story writer selected candidate: source=%s score=%s review_required=%s issue_codes=%s",
            selected.candidate.source,
            story_validation.score,
            story_validation.review_required,
            ",".join(story_validation.issue_codes) or "none",
        )
    if selected.candidate.source == "legacy_fallback":
        final_story_text = legacy_rewritten_story
        generated_story = legacy_generated_story
        rewritten_story = legacy_rewritten_story
        generation_source = "brief_driven_fallback_generation"
    else:
        final_story_text = selected.candidate.text
        generated_story = selected.candidate.text
        rewritten_story = selected.candidate.text
        generation_source = "brief_driven_candidate_generation"
    summary = (
        f"{_join_names(metadata.main_characters)} face a {metadata.hook_type.replace('_', ' ')} in the {metadata.setting}, "
        f"solve it together, and finish in a warm Buddybug ending."
    )
    review_status = _review_status_for_validation(story_validation)
    return StoryDraftPayload(
        title=idea.title,
        content_lane_key=lane_key,
        full_text=final_story_text,
        summary=summary,
        read_time_minutes=_estimate_read_time(final_story_text, lane_key=lane_key),
        review_status=review_status,
        generation_source=generation_source,
        generated_story=generated_story,
        rewritten_story=rewritten_story,
        story_brief=story_brief,
        story_validation=story_validation,
        story_outline=outline,
        illustration_scenes=illustration_scenes,
        story_metadata=metadata,
    )
