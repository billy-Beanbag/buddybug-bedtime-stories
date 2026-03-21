from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlmodel import Session, select

from app.models import Illustration, IllustrationQualityReview, StoryDraft, StoryIdea, StoryPage, StoryQualityReview
from app.services.analytics_service import track_event_safe
from app.services.review_service import set_review_status, utc_now

HIGH_SEVERITY_ISSUE_CODES = {
    "frightening_language",
    "character_attribute_mismatch",
    "character_identity_mismatch",
    "serious_age_band_mismatch",
    "missing_expected_character",
}
REVIEW_REQUIRED_THRESHOLD = 70

CANONICAL_CHARACTER_RULES: dict[str, dict[str, list[str] | str]] = {
    "verity": {
        "display_name": "Verity",
        "attributes": ["young blonde woman", "white dress", "warm mother figure"],
    },
    "dolly": {
        "display_name": "Dolly",
        "attributes": ["grey dachshund", "blue collar", "gentle expression"],
    },
    "daphne": {
        "display_name": "Daphne",
        "attributes": ["black-and-tan dachshund", "red collar", "star tag"],
    },
    "buddybug": {
        "display_name": "Buddybug",
        "attributes": ["glowing golden firefly", "warm friendly expression"],
    },
    "storylight guardians": {
        "display_name": "Storylight Guardians",
        "attributes": ["small glowing magical insect guides"],
    },
}

BEDTIME_RISK_TERMS = {
    "monster",
    "haunted",
    "terror",
    "scream",
    "blood",
    "fight",
    "attack",
    "nightmare",
}
BEDTIME_MISMATCH_TERMS = {"furious", "wild", "explosion", "battle", "chaos", "panic", "rage"}
CALM_TERMS = {"calm", "gentle", "soft", "peaceful", "warm", "sleepy", "bedtime", "cozy", "dream"}
POETIC_OVERUSE_TERMS = {
    "moonlight",
    "silver light",
    "whispering breeze",
    "soft silver",
    "glowing stars",
    "dreamy",
    "drifted like moonlight",
}
COHERENCE_BREAK_TERMS = {"suddenly", "meanwhile", "without explanation", "nobody knew why", "randomly"}
ATMOSPHERIC_OPENING_TERMS = {"moonlight", "silver light", "whispering breeze", "soft silver", "dreamy"}
PROBLEM_CUES = {"missing", "wrong", "muddle", "problem", "slipped", "wobble", "clue", "discovered", "noticed"}
RESOLUTION_CUES = {"at last", "in the end", "finally", "helped", "fixed", "solved", "found", "put things right"}
BRIGHT_PALETTE_TERMS = {"neon", "electric", "acid green", "harsh contrast"}
CALM_PALETTE_TERMS = {"soft blue", "moonlight", "warm gold", "gentle pink", "lavender", "muted"}
STYLE_CONSISTENCY_TERMS = {"storybook", "watercolor", "gentle", "soft lighting", "rounded shapes"}
PAGE_BRIEF_FIELD_LABELS = {
    "page number:",
    "exact text:",
    "scene location:",
    "characters present:",
    "key action:",
    "emotional tone:",
    "important objects:",
    "time of day and lighting:",
    "composition note:",
    "continuity notes:",
}
CHARACTER_IDENTITY_FORBIDDEN_TERMS: dict[str, tuple[str, ...]] = {
    "dolly": ("rabbit", "bunny", "hare", "bear"),
    "daphne": ("rabbit", "bunny", "hare", "bear"),
    "buddybug": ("rabbit", "bunny", "bear", "dog"),
}


@dataclass(frozen=True)
class QualityIssueSignal:
    code: str
    message: str
    severity: str
    deduction: int


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _token_hits(text: str, tokens: set[str]) -> set[str]:
    lowered = _normalize_text(text)
    hits: set[str] = set()
    for token in tokens:
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            hits.add(token)
    return hits


def _split_names(raw_value: str | None) -> set[str]:
    if not raw_value:
        return set()
    return {item.strip().lower() for item in raw_value.split(",") if item and item.strip()}


def _serialize_issue_messages(issues: list[QualityIssueSignal]) -> str:
    return json.dumps([issue.message for issue in issues], sort_keys=True)


def _parse_issue_messages(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed if isinstance(item, str)]


def _extract_prompt_field(prompt: str, label: str) -> str | None:
    lowered_label = label.casefold()
    for line in prompt.splitlines():
        stripped = line.strip()
        if stripped.casefold().startswith(lowered_label):
            return stripped.split(":", 1)[1].strip() if ":" in stripped else ""
    return None


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def _get_story_or_404(session: Session, story_id: int) -> StoryDraft:
    story = session.get(StoryDraft, story_id)
    if story is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return story


def _get_illustration_or_404(session: Session, illustration_id: int) -> Illustration:
    illustration = session.get(Illustration, illustration_id)
    if illustration is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Illustration not found")
    return illustration


def _get_story_idea(session: Session, story: StoryDraft) -> StoryIdea | None:
    if story.story_idea_id is None:
        return None
    return session.get(StoryIdea, story.story_idea_id)


def _get_story_pages(session: Session, story_id: int) -> list[StoryPage]:
    statement = select(StoryPage).where(StoryPage.story_draft_id == story_id).order_by(StoryPage.page_number.asc())
    return list(session.exec(statement).all())


def detect_story_length_issues(story: StoryDraft) -> list[QualityIssueSignal]:
    word_count = len((story.approved_text or story.full_text or "").split())
    target_range = (600, 800) if story.age_band == "3-7" else (700, 1600)
    issues: list[QualityIssueSignal] = []
    if word_count < target_range[0]:
        issues.append(
            QualityIssueSignal(
                code="story_too_short",
                message=f"Story length is light for the target age band at {word_count} words.",
                severity="medium",
                deduction=10,
            )
        )
    elif word_count > target_range[1]:
        issues.append(
            QualityIssueSignal(
                code="story_too_long",
                message=f"Story length is heavier than expected for the target age band at {word_count} words.",
                severity="medium",
                deduction=12,
            )
        )
    return issues


def detect_story_tone_issues(story: StoryDraft) -> list[QualityIssueSignal]:
    text = story.approved_text or story.full_text or ""
    issues: list[QualityIssueSignal] = []
    risk_hits = _token_hits(text, BEDTIME_RISK_TERMS)
    mismatch_hits = _token_hits(text, BEDTIME_MISMATCH_TERMS)
    calm_hits = _token_hits(text, CALM_TERMS)
    poetic_hits = _token_hits(text, POETIC_OVERUSE_TERMS)
    if risk_hits:
        issues.append(
            QualityIssueSignal(
                code="frightening_language",
                message=f"Potentially frightening or conflict-heavy terms detected: {', '.join(sorted(risk_hits))}.",
                severity="high",
                deduction=24,
            )
        )
    if story.content_lane_key == "bedtime_3_7" and mismatch_hits:
        issues.append(
            QualityIssueSignal(
                code="bedtime_tone_mismatch",
                message=f"Bedtime tone may be too intense because of terms like {', '.join(sorted(mismatch_hits))}.",
                severity="medium",
                deduction=16,
            )
        )
    if story.content_lane_key == "bedtime_3_7" and len(calm_hits) < 3:
        issues.append(
            QualityIssueSignal(
                code="insufficient_calm_signals",
                message="The story includes only limited calm, bedtime-friendly language cues.",
                severity="medium",
                deduction=10,
            )
        )
    if story.content_lane_key == "bedtime_3_7" and len(poetic_hits) >= 3:
        issues.append(
            QualityIssueSignal(
                code="poetic_overload",
                message=(
                    "The bedtime draft leans too heavily on atmospheric filler instead of plot beats: "
                    f"{', '.join(sorted(poetic_hits))}."
                ),
                severity="medium",
                deduction=10,
            )
        )
    return issues


def detect_age_band_mismatch(story: StoryDraft) -> list[QualityIssueSignal]:
    text = story.approved_text or story.full_text or ""
    word_count = len(text.split())
    long_sentence_hits = len([segment for segment in re.split(r"[.!?]", text) if len(segment.split()) > 28])
    issues: list[QualityIssueSignal] = []
    if story.age_band == "3-7" and (word_count > 1000 or long_sentence_hits >= 3):
        issues.append(
            QualityIssueSignal(
                code="serious_age_band_mismatch",
                message="The story reads heavier and more complex than expected for ages 3-7.",
                severity="high",
                deduction=20,
            )
        )
    elif story.age_band == "8-12" and word_count < 550:
        issues.append(
            QualityIssueSignal(
                code="light_age_band_depth",
                message="The story may be lighter than expected for ages 8-12.",
                severity="medium",
                deduction=8,
            )
        )
    return issues


def detect_narrative_coherence(story: StoryDraft) -> list[QualityIssueSignal]:
    text = story.approved_text or story.full_text or ""
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    issues: list[QualityIssueSignal] = []
    if len(paragraphs) < 4:
        issues.append(
            QualityIssueSignal(
                code="limited_story_structure",
                message="The story structure feels thin and may need a clearer beginning, middle, and end.",
                severity="medium",
                deduction=10,
            )
        )
    coherence_hits = _token_hits(text, COHERENCE_BREAK_TERMS)
    if len(coherence_hits) >= 2:
        issues.append(
            QualityIssueSignal(
                code="narrative_incoherence",
                message="The narrative includes abrupt transition signals that may reduce coherence.",
                severity="medium",
                deduction=12,
            )
        )
    return issues


def detect_story_constraint_issues(story: StoryDraft) -> list[QualityIssueSignal]:
    text = story.approved_text or story.full_text or ""
    lowered = text.casefold()
    first_sentence = re.split(r"(?<=[.!?])\s+", text.strip())[0].casefold() if text.strip() else ""
    issues: list[QualityIssueSignal] = []
    if any(term in first_sentence for term in ATMOSPHERIC_OPENING_TERMS):
        issues.append(
            QualityIssueSignal(
                code="atmospheric_opening",
                message="The story opens with atmosphere first instead of a concrete hook.",
                severity="medium",
                deduction=12,
            )
        )
    has_dialogue = bool(re.search(r'["“”]', text))
    if not has_dialogue:
        issues.append(
            QualityIssueSignal(
                code="missing_dialogue",
                message="The story does not include dialogue.",
                severity="medium",
                deduction=10,
            )
        )
    if not any(cue in lowered for cue in PROBLEM_CUES):
        issues.append(
            QualityIssueSignal(
                code="missing_clear_problem",
                message="The story does not clearly establish a child-sized problem or hook.",
                severity="high",
                deduction=16,
            )
        )
    explicit_resolution_patterns = (
        r"\b(here it is|there it is|found it|pulled .* free|wrapped .* in|back in place|smoothed .* flat|tucked .* in)\b"
    )
    has_resolution_cue = any(cue in lowered for cue in RESOLUTION_CUES) or bool(re.search(explicit_resolution_patterns, lowered))
    if not has_resolution_cue:
        issues.append(
            QualityIssueSignal(
                code="missing_resolution",
                message="The story does not clearly resolve the central problem.",
                severity="high",
                deduction=16,
            )
        )
    return issues


def detect_character_presence(session: Session, story: StoryDraft) -> list[QualityIssueSignal]:
    text = _normalize_text(story.approved_text or story.full_text)
    story_idea = _get_story_idea(session, story)
    expected_names = _split_names(story_idea.main_characters if story_idea is not None else None)
    expected_names.update(_split_names(story_idea.supporting_characters if story_idea is not None else None))
    issues: list[QualityIssueSignal] = []
    for expected_name in sorted(expected_names):
        if expected_name and expected_name not in text:
            issues.append(
                QualityIssueSignal(
                    code="missing_expected_character",
                    message=f"Expected character '{expected_name.title()}' is not clearly present in the story text.",
                    severity="high",
                    deduction=15,
                )
            )
    return issues


def detect_character_identity_issues(story: StoryDraft) -> list[QualityIssueSignal]:
    text = _normalize_text(story.approved_text or story.full_text)
    issues: list[QualityIssueSignal] = []
    for name, forbidden_terms in CHARACTER_IDENTITY_FORBIDDEN_TERMS.items():
        if name not in text:
            continue
        for forbidden in forbidden_terms:
            if re.search(rf"\b{name}\b[^.!?\n]{{0,80}}\b{re.escape(forbidden)}\b", text):
                issues.append(
                    QualityIssueSignal(
                        code="character_identity_mismatch",
                        message=f"{name.title()} is described as a {forbidden}, which conflicts with Buddybug canon.",
                        severity="high",
                        deduction=24,
                    )
                )
                break
    return issues


def compute_quality_score(*, starting_score: int = 100, issues: list[QualityIssueSignal]) -> int:
    score = starting_score
    for issue in issues:
        score -= issue.deduction
    return max(0, min(100, score))


def _story_summary_from_issues(issues: list[QualityIssueSignal], score: int) -> str:
    if not issues:
        return f"Automated review passed with a quality score of {score}."
    if score < REVIEW_REQUIRED_THRESHOLD:
        return f"Automated review flagged this story for human review with a quality score of {score}."
    return f"Automated review found a few watch items and scored the story at {score}."


def _delete_story_reviews(session: Session, *, story_id: int) -> None:
    rows = list(session.exec(select(StoryQualityReview).where(StoryQualityReview.story_id == story_id)).all())
    for row in rows:
        session.delete(row)
    if rows:
        session.commit()


def _delete_illustration_reviews(session: Session, *, illustration_id: int) -> None:
    rows = list(
        session.exec(select(IllustrationQualityReview).where(IllustrationQualityReview.illustration_id == illustration_id)).all()
    )
    for row in rows:
        session.delete(row)
    if rows:
        session.commit()


def create_story_quality_review(
    session: Session,
    *,
    story_id: int,
    quality_score: int,
    flagged_issues: list[QualityIssueSignal],
    evaluation_summary: str | None,
) -> StoryQualityReview:
    _delete_story_reviews(session, story_id=story_id)
    review = StoryQualityReview(
        story_id=story_id,
        quality_score=quality_score,
        review_required=quality_score < REVIEW_REQUIRED_THRESHOLD
        or any(issue.code in HIGH_SEVERITY_ISSUE_CODES or issue.severity == "high" for issue in flagged_issues),
        flagged_issues_json=_serialize_issue_messages(flagged_issues),
        evaluation_summary=evaluation_summary,
        evaluated_at=utc_now(),
    )
    return _persist(session, review)


def create_illustration_quality_review(
    session: Session,
    *,
    illustration_id: int,
    story_id: int | None,
    style_consistency_score: int,
    character_consistency_score: int,
    color_palette_score: int,
    flagged_issues: list[QualityIssueSignal],
) -> IllustrationQualityReview:
    _delete_illustration_reviews(session, illustration_id=illustration_id)
    average_score = round((style_consistency_score + character_consistency_score + color_palette_score) / 3)
    review = IllustrationQualityReview(
        illustration_id=illustration_id,
        story_id=story_id,
        style_consistency_score=style_consistency_score,
        character_consistency_score=character_consistency_score,
        color_palette_score=color_palette_score,
        flagged_issues_json=_serialize_issue_messages(flagged_issues),
        review_required=average_score < REVIEW_REQUIRED_THRESHOLD
        or any(issue.code in HIGH_SEVERITY_ISSUE_CODES or issue.severity == "high" for issue in flagged_issues),
        evaluated_at=utc_now(),
    )
    return _persist(session, review)


def evaluate_story_quality(
    session: Session,
    *,
    story_id: int,
    actor_user_id: int | None = None,
) -> StoryQualityReview:
    story = _get_story_or_404(session, story_id)
    issues = [
        *detect_story_length_issues(story),
        *detect_story_tone_issues(story),
        *detect_age_band_mismatch(story),
        *detect_narrative_coherence(story),
        *detect_story_constraint_issues(story),
        *detect_character_presence(session, story),
        *detect_character_identity_issues(story),
    ]
    score = compute_quality_score(issues=issues)
    review = create_story_quality_review(
        session,
        story_id=story.id,
        quality_score=score,
        flagged_issues=issues,
        evaluation_summary=_story_summary_from_issues(issues, score),
    )
    if review.review_required and story.review_status != "review_pending":
        set_review_status(session, story, "review_pending", "Flagged by automated story quality review.")
    track_event_safe(
        session,
        event_name="story_quality_review_completed",
        user_id=actor_user_id,
        metadata={"story_id": story.id, "quality_score": review.quality_score, "review_required": review.review_required},
    )
    if review.review_required:
        track_event_safe(
            session,
            event_name="story_flagged_for_review",
            user_id=actor_user_id,
            metadata={"story_id": story.id, "quality_score": review.quality_score},
        )
    return review


def _expected_character_names_for_page(session: Session, story: StoryDraft, page: StoryPage) -> set[str]:
    expected = _split_names(page.characters_present)
    idea = _get_story_idea(session, story)
    expected.update(_split_names(idea.main_characters if idea is not None else None))
    return expected


def evaluate_visual_style_consistency(*, story: StoryDraft, page: StoryPage, illustration: Illustration) -> tuple[int, list[QualityIssueSignal]]:
    combined_text = " ".join(
        [story.title, story.summary, page.scene_summary, page.mood, page.illustration_prompt, illustration.prompt_used]
    )
    issues: list[QualityIssueSignal] = []
    score = 100
    style_hits = _token_hits(combined_text, STYLE_CONSISTENCY_TERMS)
    if len(style_hits) < 2:
        issues.append(
            QualityIssueSignal(
                code="style_consistency_soft_warning",
                message="Illustration prompt lacks a few familiar Buddybug storybook style cues.",
                severity="medium",
                deduction=16,
            )
        )
        score -= 16
    if story.content_lane_key == "bedtime_3_7" and page.mood.lower() not in CALM_TERMS:
        issues.append(
            QualityIssueSignal(
                code="visual_calmness_mismatch",
                message="Bedtime illustration context may not feel calm enough for the story lane.",
                severity="medium",
                deduction=14,
            )
        )
        score -= 14
    prompt_lower = (illustration.prompt_used or page.illustration_prompt).lower()
    missing_labels = sorted(label for label in PAGE_BRIEF_FIELD_LABELS if label not in prompt_lower)
    if missing_labels:
        issues.append(
            QualityIssueSignal(
                code="page_brief_incomplete",
                message="Illustration prompt is missing some page-aware brief fields.",
                severity="medium",
                deduction=14,
            )
        )
        score -= 14
    return max(0, score), issues


def _evaluate_character_consistency(
    session: Session,
    *,
    story: StoryDraft,
    page: StoryPage,
    illustration: Illustration,
) -> tuple[int, list[QualityIssueSignal]]:
    combined_text = " ".join([page.characters_present, page.illustration_prompt, illustration.prompt_used]).lower()
    issues: list[QualityIssueSignal] = []
    score = 100
    expected_names = _expected_character_names_for_page(session, story, page)
    for name in sorted(expected_names):
        if name not in combined_text:
            issues.append(
                QualityIssueSignal(
                    code="missing_expected_character",
                    message=f"Illustration prompt is missing expected character '{name.title()}'.",
                    severity="high",
                    deduction=24,
                )
            )
            score -= 24
    for key, metadata in CANONICAL_CHARACTER_RULES.items():
        if key not in combined_text:
            continue
        matched = False
        for attribute in metadata["attributes"]:
            attribute_tokens = {token for token in re.split(r"[\s-]+", str(attribute).lower()) if len(token) > 2}
            if any(token in combined_text for token in attribute_tokens):
                matched = True
                break
        if not matched:
            issues.append(
                QualityIssueSignal(
                    code="character_attribute_mismatch",
                    message=f"{metadata['display_name']} appears without expected canonical visual cues.",
                    severity="high",
                    deduction=20,
                )
            )
            score -= 20
    prompt_text = " ".join([page.illustration_prompt, illustration.prompt_used]).lower()
    if re.search(r"\bdaphne\b[^.!?\n]{0,120}\bblue collar\b", prompt_text):
        issues.append(
            QualityIssueSignal(
                code="character_attribute_mismatch",
                message="Daphne is paired with a blue collar in the illustration brief, which conflicts with canon.",
                severity="high",
                deduction=24,
            )
        )
        score -= 24
    if re.search(r"\bdolly\b[^.!?\n]{0,120}\bred collar\b", prompt_text):
        issues.append(
            QualityIssueSignal(
                code="character_attribute_mismatch",
                message="Dolly is paired with a red collar in the illustration brief, which conflicts with canon.",
                severity="high",
                deduction=24,
            )
        )
        score -= 24
    return max(0, score), issues


def _evaluate_color_palette_consistency(
    *,
    story: StoryDraft,
    page: StoryPage,
    illustration: Illustration,
) -> tuple[int, list[QualityIssueSignal]]:
    combined_text = " ".join([story.summary, page.mood, page.illustration_prompt, illustration.prompt_used]).lower()
    issues: list[QualityIssueSignal] = []
    score = 100
    bright_hits = _token_hits(combined_text, BRIGHT_PALETTE_TERMS)
    calm_palette_hits = _token_hits(combined_text, CALM_PALETTE_TERMS)
    if bright_hits:
        issues.append(
            QualityIssueSignal(
                code="strong_palette_deviation",
                message=f"Illustration prompt suggests a stronger palette than expected: {', '.join(sorted(bright_hits))}.",
                severity="medium",
                deduction=18,
            )
        )
        score -= 18
    if story.content_lane_key == "bedtime_3_7" and not calm_palette_hits:
        issues.append(
            QualityIssueSignal(
                code="limited_calm_palette_cues",
                message="Bedtime illustration prompt does not include many soft or calming palette cues.",
                severity="medium",
                deduction=12,
            )
        )
        score -= 12
    return max(0, score), issues


def _evaluate_page_brief_continuity(
    session: Session,
    *,
    story: StoryDraft,
    page: StoryPage,
    illustration: Illustration,
) -> tuple[int, list[QualityIssueSignal]]:
    issues: list[QualityIssueSignal] = []
    score = 100
    prompt = illustration.prompt_used or page.illustration_prompt
    key_action = _extract_prompt_field(prompt, "Key action:")
    if not key_action:
        issues.append(
            QualityIssueSignal(
                code="missing_key_action",
                message="Illustration prompt does not clearly identify one main visual action for the page.",
                severity="high",
                deduction=20,
            )
        )
        score -= 20

    composition_note = _extract_prompt_field(prompt, "Composition note:")
    pages = _get_story_pages(session, story.id)
    adjacent_compositions = []
    for other_page in pages:
        if other_page.id == page.id or abs(other_page.page_number - page.page_number) != 1:
            continue
        adjacent_note = _extract_prompt_field(other_page.illustration_prompt, "Composition note:")
        if adjacent_note:
            adjacent_compositions.append(adjacent_note)
    if composition_note and composition_note in adjacent_compositions:
        issues.append(
            QualityIssueSignal(
                code="duplicated_composition_risk",
                message="This page shares the same composition note as an adjacent page, which risks visual repetition.",
                severity="medium",
                deduction=12,
            )
        )
        score -= 12
    return max(0, score), issues


def evaluate_illustration_quality(
    session: Session,
    *,
    illustration_id: int,
    actor_user_id: int | None = None,
) -> IllustrationQualityReview:
    illustration = _get_illustration_or_404(session, illustration_id)
    page = session.get(StoryPage, illustration.story_page_id)
    if page is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story page not found for illustration")
    story = _get_story_or_404(session, page.story_draft_id)
    style_score, style_issues = evaluate_visual_style_consistency(story=story, page=page, illustration=illustration)
    character_score, character_issues = _evaluate_character_consistency(
        session,
        story=story,
        page=page,
        illustration=illustration,
    )
    color_score, color_issues = _evaluate_color_palette_consistency(story=story, page=page, illustration=illustration)
    brief_score, brief_issues = _evaluate_page_brief_continuity(
        session,
        story=story,
        page=page,
        illustration=illustration,
    )
    issues = [*style_issues, *character_issues, *color_issues, *brief_issues]
    review = create_illustration_quality_review(
        session,
        illustration_id=illustration.id,
        story_id=story.id,
        style_consistency_score=min(style_score, brief_score),
        character_consistency_score=character_score,
        color_palette_score=color_score,
        flagged_issues=issues,
    )
    if review.review_required and story.review_status != "review_pending":
        set_review_status(session, story, "review_pending", "Flagged by automated illustration consistency review.")
    track_event_safe(
        session,
        event_name="illustration_quality_review_completed",
        user_id=actor_user_id,
        metadata={
            "illustration_id": illustration.id,
            "story_id": story.id,
            "style_consistency_score": style_score,
            "character_consistency_score": character_score,
            "color_palette_score": color_score,
            "review_required": review.review_required,
        },
    )
    if review.review_required:
        track_event_safe(
            session,
            event_name="story_flagged_for_review",
            user_id=actor_user_id,
            metadata={"story_id": story.id, "illustration_id": illustration.id, "source": "illustration_quality_review"},
        )
    return review


def get_latest_story_quality_review(session: Session, *, story_id: int) -> StoryQualityReview | None:
    statement = select(StoryQualityReview).where(StoryQualityReview.story_id == story_id).order_by(StoryQualityReview.evaluated_at.desc())
    return session.exec(statement).first()


def get_latest_illustration_quality_reviews(session: Session, *, story_id: int) -> list[IllustrationQualityReview]:
    statement = (
        select(IllustrationQualityReview)
        .where(IllustrationQualityReview.story_id == story_id)
        .order_by(IllustrationQualityReview.evaluated_at.desc(), IllustrationQualityReview.id.desc())
    )
    return list(session.exec(statement).all())


def get_or_create_story_quality_review(session: Session, *, story_id: int) -> StoryQualityReview:
    existing = get_latest_story_quality_review(session, story_id=story_id)
    if existing is not None:
        return existing
    return evaluate_story_quality(session, story_id=story_id)


def build_story_quality_summary(session: Session, *, story_id: int) -> dict[str, object]:
    review = get_or_create_story_quality_review(session, story_id=story_id)
    illustration_reviews = get_latest_illustration_quality_reviews(session, story_id=story_id)
    flagged_issues = _parse_issue_messages(review.flagged_issues_json)
    for item in illustration_reviews:
        flagged_issues.extend(_parse_issue_messages(item.flagged_issues_json))
    deduped_issues = list(dict.fromkeys(flagged_issues))
    review_required = review.review_required or any(item.review_required for item in illustration_reviews)
    if illustration_reviews:
        illustration_average = min(
            round((item.style_consistency_score + item.character_consistency_score + item.color_palette_score) / 3)
            for item in illustration_reviews
        )
        quality_score = min(review.quality_score, illustration_average)
    else:
        quality_score = review.quality_score
    return {
        "story_id": story_id,
        "quality_score": quality_score,
        "review_required": review_required,
        "flagged_issues": deduped_issues,
    }


def list_story_quality_review_queue(session: Session) -> list[dict[str, object]]:
    story_reviews = list(
        session.exec(
            select(StoryQualityReview).where(StoryQualityReview.review_required.is_(True)).order_by(StoryQualityReview.evaluated_at.desc())
        ).all()
    )
    illustration_reviews = list(
        session.exec(
            select(IllustrationQualityReview)
            .where(IllustrationQualityReview.review_required.is_(True), IllustrationQualityReview.story_id != None)  # noqa: E711
            .order_by(IllustrationQualityReview.evaluated_at.desc())
        ).all()
    )
    story_ids: list[int] = []
    for review in story_reviews:
        if review.story_id not in story_ids:
            story_ids.append(review.story_id)
    for review in illustration_reviews:
        if review.story_id is not None and review.story_id not in story_ids:
            story_ids.append(review.story_id)
    items: list[dict[str, object]] = []
    for story_id in story_ids:
        story = session.get(StoryDraft, story_id)
        if story is None:
            continue
        summary = build_story_quality_summary(session, story_id=story_id)
        review = get_latest_story_quality_review(session, story_id=story_id)
        items.append(
            {
                "story_id": story.id,
                "title": story.title,
                "review_status": story.review_status,
                "quality_score": summary["quality_score"],
                "review_required": summary["review_required"],
                "flagged_issues": summary["flagged_issues"],
                "evaluation_summary": review.evaluation_summary if review is not None else None,
                "evaluated_at": review.evaluated_at if review is not None else utc_now(),
            }
        )
    items.sort(key=lambda item: (item["evaluated_at"], -int(item["quality_score"])), reverse=True)
    return items
