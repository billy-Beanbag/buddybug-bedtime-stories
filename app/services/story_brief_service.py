from __future__ import annotations

import json

from sqlmodel import Session, select

from app.models import StoryBrief as StoryBriefRecord
from app.schemas.story_pipeline_schema import StoryBrief


def get_story_brief_record(session: Session, *, story_idea_id: int) -> StoryBriefRecord | None:
    statement = select(StoryBriefRecord).where(StoryBriefRecord.story_idea_id == story_idea_id)
    return session.exec(statement).first()


def upsert_story_brief_record(
    session: Session,
    *,
    story_idea_id: int,
    story_brief: StoryBrief,
) -> StoryBriefRecord:
    row = get_story_brief_record(session, story_idea_id=story_idea_id)
    payload_json = json.dumps(story_brief.model_dump(), sort_keys=True)
    if row is None:
        row = StoryBriefRecord(
            story_idea_id=story_idea_id,
            mode=story_brief.mode,
            hook_type=story_brief.hook_type,
            target_age_band=story_brief.target_age_band,
            tone=story_brief.tone,
            brief_json=payload_json,
        )
    else:
        row.mode = story_brief.mode
        row.hook_type = story_brief.hook_type
        row.target_age_band = story_brief.target_age_band
        row.tone = story_brief.tone
        row.brief_json = payload_json
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
