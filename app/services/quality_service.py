from __future__ import annotations

import json
import re
from statistics import mean
from typing import Iterable

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import QualityCheck, StoryDraft, StoryIdea, StoryPage
from app.schemas.quality_schema import QualityIssue
from app.services.content_lane_service import resolve_content_lane_key
from app.utils.seed_content_lanes import BEDTIME_3_7_LANE_KEY, STORY_ADVENTURES_8_12_LANE_KEY
QUALITY_TARGET_TYPES = {"story_draft", "story_pages", "book"}
QUALITY_CHECK_TYPES = {
    "bedtime_safety",
    "age_appropriateness",
    "character_consistency",
    "style_consistency",
    "structure_quality",
    "overall_quality",
}
QUALITY_STATUSES = {"passed", "warning", "failed"}

CANONICAL_CHARACTERS = {
    "verity",
    "dolly",
    "daphne",
    "buddybug",
    "glowmoth",
    "twinklet",
    "whisperwing",
}
LIKELY_MISSPELLINGS = {
    "verrity": "Verity",
    "dolley": "Dolly",
    "daphnie": "Daphne",
    "budybug": "Buddybug",
    "buddy bug": "Buddybug",
    "glow moth": "Glowmoth",
    "glowmothh": "Glowmoth",
    "twinklett": "Twinklet",
    "whisper wing": "Whisperwing",
}
SEVERE_BEDTIME_RISKS = {
    "kill",
    "dead",
    "death",
    "blood",
    "attack",
    "monster",
    "demon",
    "nightmare",
    "scream",
    "weapon",
    "gun",
    "knife",
    "fight",
    "poison",
    "haunted",
    "terror",
}
BEDTIME_MILD_RISKS = {"darkness", "fright", "panic", "chase", "cry", "scary", "spooky"}
ADVENTURE_MILD_RISKS = {"panic", "scary", "spooky"}
ADULT_OR_INAPPROPRIATE_TOPICS = {"alcohol", "drunk", "drugs", "romance", "kissed passionately", "gambling"}
ADVANCED_VOCABULARY = {
    "melancholy",
    "catastrophe",
    "obliterated",
    "devastation",
    "intergalactic",
    "quantum",
    "apocalypse",
    "ferocious",
    "treacherous",
}
BEDTIME_STYLE_BREAK_WORDS = {
    "exploded",
    "battle",
    "laser",
    "apocalypse",
    "zombie",
    "furious",
    "extreme",
    "savage",
    "panic",
    "raced wildly",
    "adrenaline",
}
ADVENTURE_STYLE_BREAK_WORDS = {"apocalypse", "zombie", "savage", "laser", "furious", "extreme", "gory"}
CALM_ENDING_CUES = {"sleep", "sleepy", "dream", "rest", "peaceful", "calm", "soft", "gentle", "bedtime", "lullaby"}
POSITIVE_RESOLUTION_CUES = {"solved", "understood", "together", "hope", "home", "learned", "shared", "safe"}
HOOK_CUES = {"missing", "noticed", "discovered", "muddle", "clue", "problem", "shortcut", "surprise", "odd", "wrong"}
POETIC_FILLER_CUES = {"moonlight", "glowing stars", "whispering breeze", "silver light", "dreamy", "soft silver"}


def _validate_target_type(target_type: str) -> str:
    if target_type not in QUALITY_TARGET_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quality target_type")
    return target_type


def _validate_check_type(check_type: str) -> str:
    if check_type not in QUALITY_CHECK_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quality check_type")
    return check_type


def _validate_status(status_value: str) -> str:
    if status_value not in QUALITY_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quality status")
    return status_value


def _serialize_issues(issues: list[QualityIssue]) -> str | None:
    if not issues:
        return None
    return json.dumps([issue.model_dump() for issue in issues], sort_keys=True)


def _persist_checks(session: Session, checks: list[QualityCheck]) -> list[QualityCheck]:
    for check in checks:
        session.add(check)
    session.commit()
    for check in checks:
        session.refresh(check)
    return checks


def delete_existing_checks_for_target(session: Session, *, target_type: str, target_id: int) -> None:
    _validate_target_type(target_type)
    existing = list(
        session.exec(
            select(QualityCheck).where(QualityCheck.target_type == target_type, QualityCheck.target_id == target_id)
        ).all()
    )
    for item in existing:
        session.delete(item)
    session.commit()


def get_quality_checks_for_target(
    session: Session,
    *,
    target_type: str,
    target_id: int,
) -> list[QualityCheck]:
    _validate_target_type(target_type)
    return list(
        session.exec(
            select(QualityCheck)
            .where(QualityCheck.target_type == target_type, QualityCheck.target_id == target_id)
            .order_by(QualityCheck.created_at.asc(), QualityCheck.id.asc())
        ).all()
    )


def list_quality_checks(
    session: Session,
    *,
    target_type: str | None,
    target_id: int | None,
    check_type: str | None,
    status_value: str | None,
    limit: int,
) -> list[QualityCheck]:
    statement = select(QualityCheck).order_by(QualityCheck.created_at.desc()).limit(limit)
    if target_type:
        _validate_target_type(target_type)
        statement = statement.where(QualityCheck.target_type == target_type)
    if target_id is not None:
        statement = statement.where(QualityCheck.target_id == target_id)
    if check_type:
        _validate_check_type(check_type)
        statement = statement.where(QualityCheck.check_type == check_type)
    if status_value:
        _validate_status(status_value)
        statement = statement.where(QualityCheck.status == status_value)
    return list(session.exec(statement).all())


def _text_to_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _normalize_text(text: str) -> str:
    return text.casefold()


def _keyword_hits(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = _normalize_text(text)
    hits: list[str] = []
    for keyword in keywords:
        escaped = re.escape(keyword)
        pattern = rf"\b{escaped}\b" if re.fullmatch(r"[\w-]+", keyword) else escaped
        if re.search(pattern, lowered):
            hits.append(keyword)
    return hits


def _build_check(
    *,
    target_type: str,
    target_id: int,
    check_type: str,
    status_value: str,
    summary: str,
    issues: list[QualityIssue],
    score: float | None = None,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    return QualityCheck(
        target_type=_validate_target_type(target_type),
        target_id=target_id,
        check_type=_validate_check_type(check_type),
        status=_validate_status(status_value),
        score=score,
        issues_json=_serialize_issues(issues),
        summary=summary,
        created_by_job_id=created_by_job_id,
    )


def _get_story_draft_or_404(session: Session, story_draft_id: int) -> StoryDraft:
    draft = session.get(StoryDraft, story_draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    return draft


def _get_story_idea_for_draft(session: Session, story_draft: StoryDraft) -> StoryIdea | None:
    if story_draft.story_idea_id is None:
        return None
    return session.get(StoryIdea, story_draft.story_idea_id)


def _lane_key_for_story_draft(session: Session, story_draft: StoryDraft) -> str:
    story_idea = _get_story_idea_for_draft(session, story_draft)
    return resolve_content_lane_key(
        story_idea.age_band if story_idea is not None else None,
        story_draft.content_lane_key or (story_idea.content_lane_key if story_idea is not None else None),
    )


def _get_story_pages_for_draft(session: Session, story_draft_id: int) -> list[StoryPage]:
    return list(
        session.exec(
            select(StoryPage).where(StoryPage.story_draft_id == story_draft_id).order_by(StoryPage.page_number)
        ).all()
    )


def _draft_text(story_draft: StoryDraft) -> str:
    return (story_draft.approved_text or story_draft.full_text or "").strip()


def check_bedtime_safety(
    target_type: str,
    target_id: int,
    text: str,
    *,
    lane_key: str,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    severe_hits = _keyword_hits(text, SEVERE_BEDTIME_RISKS)
    mild_hits = _keyword_hits(
        text,
        BEDTIME_MILD_RISKS if lane_key == BEDTIME_3_7_LANE_KEY else ADVENTURE_MILD_RISKS,
    )
    issues: list[QualityIssue] = []
    status_value = "passed"
    summary = (
        "No obvious scary or bedtime-inappropriate language detected."
        if lane_key == BEDTIME_3_7_LANE_KEY
        else "No obvious graphic or horror-oriented language detected."
    )
    if len(severe_hits) >= 2:
        status_value = "failed"
        issues.append(
            QualityIssue(
                code="severe_bedtime_risk",
                message=f"Repeated risky terms detected: {', '.join(sorted(set(severe_hits)))}.",
                severity="high",
            )
        )
        summary = "Repeated scary or violent language was detected."
    elif severe_hits or mild_hits:
        status_value = "warning"
        detected = sorted(set(severe_hits + mild_hits))
        issues.append(
            QualityIssue(
                code="bedtime_risk_keywords",
                message=f"Potentially unsuitable bedtime terms detected: {', '.join(detected)}.",
                severity="medium",
            )
        )
        summary = (
            "Potential bedtime-safety concerns were detected."
            if lane_key == BEDTIME_3_7_LANE_KEY
            else "Potential adventure-safety concerns were detected."
        )
    score = 1.0 if status_value == "passed" else 0.6 if status_value == "warning" else 0.2
    return _build_check(
        target_type=target_type,
        target_id=target_id,
        check_type="bedtime_safety",
        status_value=status_value,
        summary=summary,
        issues=issues,
        score=score,
        created_by_job_id=created_by_job_id,
    )


def check_age_appropriateness(
    target_type: str,
    target_id: int,
    text: str,
    *,
    expected_min_words: int,
    expected_max_words: int,
    lane_key: str,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    words = text.split()
    word_count = len(words)
    sentences = _text_to_sentences(text)
    avg_sentence_length = mean(len(sentence.split()) for sentence in sentences) if sentences else 0
    advanced_hits = _keyword_hits(text, ADVANCED_VOCABULARY)
    inappropriate_hits = _keyword_hits(text, ADULT_OR_INAPPROPRIATE_TOPICS)
    issues: list[QualityIssue] = []
    status_value = "passed"
    summary = (
        "Length and language appear appropriate for ages 3-7."
        if lane_key == BEDTIME_3_7_LANE_KEY
        else "Length and language appear appropriate for ages 8-12."
    )
    if inappropriate_hits:
        status_value = "failed"
        issues.append(
            QualityIssue(
                code="inappropriate_theme",
                message=f"Inappropriate themes or phrases detected: {', '.join(sorted(set(inappropriate_hits)))}.",
                severity="high",
            )
        )
        summary = "Clearly unsuitable age-inappropriate themes were detected."
    else:
        if word_count < expected_min_words or word_count > expected_max_words:
            issues.append(
                QualityIssue(
                    code="length_out_of_range",
                    message=f"Word count {word_count} is outside the preferred range of {expected_min_words}-{expected_max_words}.",
                    severity="medium",
                )
            )
        max_sentence_length = 22 if lane_key == BEDTIME_3_7_LANE_KEY else 30
        if avg_sentence_length > max_sentence_length:
            issues.append(
                QualityIssue(
                    code="sentence_complexity",
                    message=(
                        f"Average sentence length is {avg_sentence_length:.1f} words, which may be too complex for ages 3-7."
                        if lane_key == BEDTIME_3_7_LANE_KEY
                        else f"Average sentence length is {avg_sentence_length:.1f} words, which may be too complex for ages 8-12."
                    ),
                    severity="medium" if avg_sentence_length <= max_sentence_length + 8 else "high",
                )
            )
        advanced_threshold = 1 if lane_key == BEDTIME_3_7_LANE_KEY else 3
        if len(advanced_hits) >= advanced_threshold:
            issues.append(
                QualityIssue(
                    code="advanced_vocabulary",
                    message=f"Potentially advanced vocabulary detected: {', '.join(sorted(set(advanced_hits)))}.",
                    severity="medium",
                )
            )
        if any(issue.severity == "high" for issue in issues):
            status_value = "failed"
            summary = "The story may be too complex or unsuitable for the target age range."
        elif issues:
            status_value = "warning"
            summary = "The story may need age-range simplification or length adjustment."
    score = 1.0 if status_value == "passed" else 0.65 if status_value == "warning" else 0.25
    return _build_check(
        target_type=target_type,
        target_id=target_id,
        check_type="age_appropriateness",
        status_value=status_value,
        summary=summary,
        issues=issues,
        score=score,
        created_by_job_id=created_by_job_id,
    )


def check_character_consistency_for_draft(
    session: Session,
    story_draft: StoryDraft,
    *,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    text = _draft_text(story_draft)
    idea = _get_story_idea_for_draft(session, story_draft)
    expected_names = set()
    if idea is not None:
        expected_names.update(name.strip().casefold() for name in (idea.main_characters or "").split(",") if name.strip())
        expected_names.update(name.strip().casefold() for name in (idea.supporting_characters or "").split(",") if name.strip())
    present_names = {name for name in CANONICAL_CHARACTERS if name in _normalize_text(text)}
    issues: list[QualityIssue] = []
    for misspelling, correct_name in LIKELY_MISSPELLINGS.items():
        if misspelling in _normalize_text(text):
            issues.append(
                QualityIssue(
                    code="character_name_misspelling",
                    message=f"Detected likely misspelling '{misspelling}' for {correct_name}.",
                    severity="medium",
                )
            )
    missing_expected = sorted(expected_names - present_names)
    if missing_expected:
        issues.append(
            QualityIssue(
                code="expected_character_missing",
                message=f"Expected character references were not clearly found: {', '.join(name.title() for name in missing_expected)}.",
                severity="medium",
            )
        )
    status_value = "passed"
    summary = "Character references appear consistent with the Buddybug canon."
    if issues:
        status_value = "warning"
        summary = "Potential character consistency issues were detected."
    score = 1.0 if status_value == "passed" else 0.7
    return _build_check(
        target_type="story_draft",
        target_id=story_draft.id,
        check_type="character_consistency",
        status_value=status_value,
        summary=summary,
        issues=issues,
        score=score,
        created_by_job_id=created_by_job_id,
    )


def check_character_consistency_for_pages(
    session: Session,
    story_draft_id: int,
    pages: list[StoryPage],
    *,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    draft = _get_story_draft_or_404(session, story_draft_id)
    idea = _get_story_idea_for_draft(session, draft)
    expected_names = set()
    if idea is not None:
        expected_names.update(name.strip().casefold() for name in (idea.main_characters or "").split(",") if name.strip())
        expected_names.update(name.strip().casefold() for name in (idea.supporting_characters or "").split(",") if name.strip())
    page_names: set[str] = set()
    issues: list[QualityIssue] = []
    for page in pages:
        extracted = {name.strip().casefold() for name in (page.characters_present or "").split(",") if name.strip()}
        page_names.update(extracted)
        unknown = sorted(name for name in extracted if name not in CANONICAL_CHARACTERS)
        if unknown:
            issues.append(
                QualityIssue(
                    code="unknown_page_character",
                    message=f"Page {page.page_number} includes unknown character tags: {', '.join(unknown)}.",
                    severity="medium",
                )
            )
    missing_expected = sorted(expected_names - page_names)
    if missing_expected:
        issues.append(
            QualityIssue(
                code="expected_page_character_missing",
                message=f"Expected characters were not represented across page plans: {', '.join(name.title() for name in missing_expected)}.",
                severity="medium",
            )
        )
    status_value = "passed"
    summary = "Page-level character references appear consistent."
    if issues:
        status_value = "warning"
        summary = "Potential page-level character consistency issues were detected."
    return _build_check(
        target_type="story_pages",
        target_id=story_draft_id,
        check_type="character_consistency",
        status_value=status_value,
        summary=summary,
        issues=issues,
        score=1.0 if status_value == "passed" else 0.7,
        created_by_job_id=created_by_job_id,
    )


def check_style_consistency(
    target_type: str,
    target_id: int,
    text: str,
    *,
    lane_key: str,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    style_hits = _keyword_hits(
        text,
        BEDTIME_STYLE_BREAK_WORDS if lane_key == BEDTIME_3_7_LANE_KEY else ADVENTURE_STYLE_BREAK_WORDS,
    )
    issues: list[QualityIssue] = []
    status_value = "passed"
    summary = (
        "Tone and style appear aligned with the calm bedtime world."
        if lane_key == BEDTIME_3_7_LANE_KEY
        else "Tone and style appear aligned with the older-child adventure lane."
    )
    if len(style_hits) >= 3:
        status_value = "failed"
        issues.append(
            QualityIssue(
                code="major_style_break",
                message=f"Repeated off-brand style terms detected: {', '.join(sorted(set(style_hits)))}.",
                severity="high",
            )
        )
        summary = (
            "The content strongly conflicts with the Buddybug bedtime style."
            if lane_key == BEDTIME_3_7_LANE_KEY
            else "The content strongly conflicts with the safe adventure lane."
        )
    elif style_hits:
        status_value = "warning"
        issues.append(
            QualityIssue(
                code="style_break_terms",
                message=f"Potential style-breaking language detected: {', '.join(sorted(set(style_hits)))}.",
                severity="medium",
            )
        )
        summary = (
            "Some language may feel too intense or off-brand for Buddybug."
            if lane_key == BEDTIME_3_7_LANE_KEY
            else "Some language may feel too intense or off-brand for the 8-12 lane."
        )
    return _build_check(
        target_type=target_type,
        target_id=target_id,
        check_type="style_consistency",
        status_value=status_value,
        summary=summary,
        issues=issues,
        score=1.0 if status_value == "passed" else 0.6 if status_value == "warning" else 0.2,
        created_by_job_id=created_by_job_id,
    )


def check_structure_quality_for_draft(
    story_draft: StoryDraft,
    *,
    lane_key: str,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    text = _draft_text(story_draft)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    words = text.split()
    ending_window = " ".join(words[-180:]) if words else ""
    opening_window = " ".join(words[:90]) if words else ""
    ending_hits = _keyword_hits(ending_window, CALM_ENDING_CUES)
    hook_hits = _keyword_hits(opening_window, HOOK_CUES)
    poetic_hits = _keyword_hits(text, POETIC_FILLER_CUES)
    issues: list[QualityIssue] = []
    minimum_paragraphs = 4 if lane_key == BEDTIME_3_7_LANE_KEY else 5
    minimum_words = 600 if lane_key == BEDTIME_3_7_LANE_KEY else 700
    if len(paragraphs) < minimum_paragraphs:
        issues.append(
            QualityIssue(
                code="structure_too_short",
                message="The draft may not have a clear beginning, middle, and ending structure.",
                severity="medium",
            )
        )
    if len(words) < minimum_words:
        issues.append(
            QualityIssue(
                code="story_too_short",
                message="The story draft is shorter than the expected bedtime read length.",
                severity="medium",
            )
        )
    if len(hook_hits) < 1:
        issues.append(
            QualityIssue(
                code="weak_hook",
                message="The opening may need a clearer hook or concrete child-friendly problem in the first lines.",
                severity="medium",
            )
        )
    if lane_key == BEDTIME_3_7_LANE_KEY and not ending_hits:
        issues.append(
            QualityIssue(
                code="calm_ending_missing",
                message="The ending does not clearly include sleepy or calming cues.",
                severity="medium",
            )
        )
    if lane_key == BEDTIME_3_7_LANE_KEY and len(poetic_hits) >= 3:
        issues.append(
            QualityIssue(
                code="atmospheric_filler_overuse",
                message="The draft may rely too heavily on atmospheric filler instead of concrete story beats.",
                severity="medium",
            )
        )
    if lane_key == STORY_ADVENTURES_8_12_LANE_KEY:
        positive_resolution_hits = _keyword_hits(ending_window, POSITIVE_RESOLUTION_CUES)
        if not positive_resolution_hits:
            issues.append(
                QualityIssue(
                    code="positive_resolution_missing",
                    message="The ending does not clearly land on a positive solution or reflection.",
                    severity="medium",
                )
            )
    status_value = "passed" if not issues else "warning"
    summary = (
        "The story structure includes a clear gentle bedtime arc."
        if status_value == "passed" and lane_key == BEDTIME_3_7_LANE_KEY
        else "The story structure supports a satisfying older-child adventure arc."
        if status_value == "passed"
        else "The story structure may need a clearer calm ending or fuller bedtime arc."
        if lane_key == BEDTIME_3_7_LANE_KEY
        else "The story structure may need a stronger problem-solution arc or a clearer positive resolution."
    )
    return _build_check(
        target_type="story_draft",
        target_id=story_draft.id,
        check_type="structure_quality",
        status_value=status_value,
        summary=summary,
        issues=issues,
        score=1.0 if status_value == "passed" else 0.7,
        created_by_job_id=created_by_job_id,
    )


def check_structure_quality_for_pages(
    story_draft_id: int,
    pages: list[StoryPage],
    *,
    lane_key: str,
    created_by_job_id: int | None = None,
) -> QualityCheck:
    issues: list[QualityIssue] = []
    page_count = len(pages)
    minimum_pages, maximum_pages = (8, 14) if lane_key == BEDTIME_3_7_LANE_KEY else (8, 16)
    if page_count < minimum_pages or page_count > maximum_pages:
        issues.append(
            QualityIssue(
                code="page_count_out_of_range",
                message=f"Page count {page_count} is outside the preferred {minimum_pages}-{maximum_pages} page range.",
                severity="medium",
            )
        )
    sparse_pages = [page.page_number for page in pages if len((page.page_text or "").split()) < 8]
    if sparse_pages:
        issues.append(
            QualityIssue(
                code="sparse_page_text",
                message=f"Some pages have very little text: {', '.join(str(number) for number in sparse_pages)}.",
                severity="medium",
            )
        )
    dense_limit = 180 if lane_key == BEDTIME_3_7_LANE_KEY else 220
    dense_pages = [page.page_number for page in pages if len((page.page_text or "").split()) > dense_limit]
    if dense_pages:
        issues.append(
            QualityIssue(
                code="overdense_page_text",
                message=f"Some pages may be too text-heavy: {', '.join(str(number) for number in dense_pages)}.",
                severity="medium",
            )
        )
    status_value = "passed" if not issues else "warning"
    summary = (
        "The page plan structure looks balanced for a bedtime picture book."
        if status_value == "passed" and lane_key == BEDTIME_3_7_LANE_KEY
        else "The page plan structure looks balanced for an older-child illustrated adventure."
        if status_value == "passed"
        else "The page plan may need balancing for pacing or readability."
    )
    return _build_check(
        target_type="story_pages",
        target_id=story_draft_id,
        check_type="structure_quality",
        status_value=status_value,
        summary=summary,
        issues=issues,
        score=1.0 if status_value == "passed" else 0.7,
        created_by_job_id=created_by_job_id,
    )


def build_overall_quality_check(
    *,
    target_type: str,
    target_id: int,
    checks: list[QualityCheck],
    created_by_job_id: int | None = None,
) -> QualityCheck:
    statuses = [check.status for check in checks if check.check_type != "overall_quality"]
    if any(status_value == "failed" for status_value in statuses):
        overall_status = "failed"
        summary = "One or more quality checks failed."
    elif any(status_value == "warning" for status_value in statuses):
        overall_status = "warning"
        summary = "One or more quality checks raised warnings."
    else:
        overall_status = "passed"
        summary = "All quality checks passed."
    score_values = [check.score for check in checks if check.score is not None and check.check_type != "overall_quality"]
    overall_score = round(mean(score_values), 2) if score_values else None
    return _build_check(
        target_type=target_type,
        target_id=target_id,
        check_type="overall_quality",
        status_value=overall_status,
        summary=summary,
        issues=[],
        score=overall_score,
        created_by_job_id=created_by_job_id,
    )


def run_story_draft_quality_checks(
    session: Session,
    *,
    story_draft_id: int,
    created_by_job_id: int | None = None,
) -> list[QualityCheck]:
    story_draft = _get_story_draft_or_404(session, story_draft_id)
    text = _draft_text(story_draft)
    lane_key = _lane_key_for_story_draft(session, story_draft)
    delete_existing_checks_for_target(session, target_type="story_draft", target_id=story_draft.id)
    checks = [
        check_bedtime_safety(
            "story_draft",
            story_draft.id,
            text,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
        check_age_appropriateness(
            "story_draft",
            story_draft.id,
            text,
            expected_min_words=600 if lane_key == BEDTIME_3_7_LANE_KEY else 850,
            expected_max_words=800 if lane_key == BEDTIME_3_7_LANE_KEY else 1800,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
        check_character_consistency_for_draft(session, story_draft, created_by_job_id=created_by_job_id),
        check_style_consistency(
            "story_draft",
            story_draft.id,
            text,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
        check_structure_quality_for_draft(
            story_draft,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
    ]
    checks.append(
        build_overall_quality_check(
            target_type="story_draft",
            target_id=story_draft.id,
            checks=checks,
            created_by_job_id=created_by_job_id,
        )
    )
    return _persist_checks(session, checks)


def run_story_pages_quality_checks(
    session: Session,
    *,
    story_draft_id: int,
    created_by_job_id: int | None = None,
) -> list[QualityCheck]:
    story_draft = _get_story_draft_or_404(session, story_draft_id)
    lane_key = _lane_key_for_story_draft(session, story_draft)
    pages = _get_story_pages_for_draft(session, story_draft_id)
    if not pages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Story pages do not exist for this draft")
    combined_text = "\n\n".join(
        f"{page.page_text}\n{page.scene_summary}\n{page.location}\n{page.mood}\n{page.characters_present}"
        for page in pages
    )
    delete_existing_checks_for_target(session, target_type="story_pages", target_id=story_draft_id)
    checks = [
        check_bedtime_safety(
            "story_pages",
            story_draft_id,
            combined_text,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
        check_age_appropriateness(
            "story_pages",
            story_draft_id,
            combined_text,
            expected_min_words=200 if lane_key == BEDTIME_3_7_LANE_KEY else 250,
            expected_max_words=2500 if lane_key == BEDTIME_3_7_LANE_KEY else 3200,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
        check_character_consistency_for_pages(
            session,
            story_draft_id,
            pages,
            created_by_job_id=created_by_job_id,
        ),
        check_style_consistency(
            "story_pages",
            story_draft_id,
            combined_text,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
        check_structure_quality_for_pages(
            story_draft_id,
            pages,
            lane_key=lane_key,
            created_by_job_id=created_by_job_id,
        ),
    ]
    checks.append(
        build_overall_quality_check(
            target_type="story_pages",
            target_id=story_draft_id,
            checks=checks,
            created_by_job_id=created_by_job_id,
        )
    )
    return _persist_checks(session, checks)


def get_overall_quality_status(
    session: Session,
    *,
    target_type: str,
    target_id: int,
) -> str:
    checks = get_quality_checks_for_target(session, target_type=target_type, target_id=target_id)
    overall = next((check for check in checks if check.check_type == "overall_quality"), None)
    if overall is not None:
        return overall.status
    if any(check.status == "failed" for check in checks):
        return "failed"
    if any(check.status == "warning" for check in checks):
        return "warning"
    return "passed"
