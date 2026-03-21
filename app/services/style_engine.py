from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, select

from app.models import StoryDraft, StoryStyleTrainingData


@dataclass(frozen=True)
class StyleReferenceExample:
    title: str
    text: str


def queue_story_edit_training_record(
    session: Session,
    *,
    original_story: str,
    edited_story: str,
    edit_notes: str | None,
) -> StoryStyleTrainingData | None:
    """Queue a new founder edit example in the current session if the text really changed."""
    original = (original_story or "").strip()
    edited = (edited_story or "").strip()
    if not original or not edited or original == edited:
        return None
    row = StoryStyleTrainingData(
        original_story=original,
        edited_story=edited,
        edit_notes=(edit_notes or "").strip() or None,
    )
    session.add(row)
    return row


def list_style_reference_examples(
    session: Session,
    *,
    age_band: str,
    content_lane_key: str | None,
    limit: int = 3,
) -> list[StyleReferenceExample]:
    """Return 2-3 previously approved Buddybug stories as style references."""
    statement = (
        select(StoryDraft)
        .where(StoryDraft.age_band == age_band, StoryDraft.review_status == "approved_for_illustration")
        .order_by(StoryDraft.updated_at.desc())
        .limit(limit * 2)
    )
    if content_lane_key is not None:
        statement = statement.where(StoryDraft.content_lane_key == content_lane_key)

    examples: list[StyleReferenceExample] = []
    for draft in session.exec(statement).all():
        text = (draft.approved_text or draft.full_text or "").strip()
        if not text:
            continue
        examples.append(StyleReferenceExample(title=draft.title, text=text))
        if len(examples) >= limit:
            break
    return examples


def build_style_reference_block(examples: list[StyleReferenceExample]) -> str:
    """Render style examples in the future-facing prompt/reference format requested by the product."""
    sections: list[str] = []
    for index, example in enumerate(examples, start=1):
        sections.append(f"Example Buddybug Story {index}\nTitle: {example.title}\n{example.text}")
    return "\n\n".join(sections)
