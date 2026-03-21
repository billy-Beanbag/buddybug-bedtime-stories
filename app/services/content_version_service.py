from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import StoryDraft, StoryDraftVersion, StoryPage, StoryPageVersion


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _next_draft_version_number(session: Session, *, story_draft_id: int) -> int:
    versions = list(
        session.exec(
            select(StoryDraftVersion)
            .where(StoryDraftVersion.story_draft_id == story_draft_id)
            .order_by(StoryDraftVersion.version_number.desc())
        ).all()
    )
    return (versions[0].version_number + 1) if versions else 1


def _next_page_version_number(session: Session, *, story_page_id: int) -> int:
    versions = list(
        session.exec(
            select(StoryPageVersion)
            .where(StoryPageVersion.story_page_id == story_page_id)
            .order_by(StoryPageVersion.version_number.desc())
        ).all()
    )
    return (versions[0].version_number + 1) if versions else 1


def snapshot_story_draft(
    session: Session,
    *,
    story_draft: StoryDraft,
    created_by_user_id: int | None = None,
) -> StoryDraftVersion:
    version = StoryDraftVersion(
        story_draft_id=story_draft.id,
        version_number=_next_draft_version_number(session, story_draft_id=story_draft.id),
        title=story_draft.title,
        full_text=story_draft.full_text,
        summary=story_draft.summary,
        review_status=story_draft.review_status,
        review_notes=story_draft.review_notes,
        approved_text=story_draft.approved_text,
        created_by_user_id=created_by_user_id,
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def snapshot_story_page(
    session: Session,
    *,
    story_page: StoryPage,
    created_by_user_id: int | None = None,
) -> StoryPageVersion:
    version = StoryPageVersion(
        story_page_id=story_page.id,
        version_number=_next_page_version_number(session, story_page_id=story_page.id),
        page_number=story_page.page_number,
        page_text=story_page.page_text,
        scene_summary=story_page.scene_summary,
        location=story_page.location,
        mood=story_page.mood,
        characters_present=story_page.characters_present,
        illustration_prompt=story_page.illustration_prompt,
        image_url=story_page.image_url,
        created_by_user_id=created_by_user_id,
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def list_story_draft_versions(session: Session, *, draft_id: int) -> list[StoryDraftVersion]:
    return list(
        session.exec(
            select(StoryDraftVersion)
            .where(StoryDraftVersion.story_draft_id == draft_id)
            .order_by(StoryDraftVersion.version_number.desc(), StoryDraftVersion.created_at.desc())
        ).all()
    )


def list_story_page_versions(session: Session, *, page_id: int) -> list[StoryPageVersion]:
    return list(
        session.exec(
            select(StoryPageVersion)
            .where(StoryPageVersion.story_page_id == page_id)
            .order_by(StoryPageVersion.version_number.desc(), StoryPageVersion.created_at.desc())
        ).all()
    )


def get_story_draft_version_or_404(session: Session, *, version_id: int) -> StoryDraftVersion:
    version = session.get(StoryDraftVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft version not found")
    return version


def get_story_page_version_or_404(session: Session, *, version_id: int) -> StoryPageVersion:
    version = session.get(StoryPageVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story page version not found")
    return version


def rollback_story_draft(
    session: Session,
    *,
    story_draft: StoryDraft,
    version: StoryDraftVersion,
    created_by_user_id: int | None = None,
) -> StoryDraft:
    if version.story_draft_id != story_draft.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version does not belong to this story draft")
    snapshot_story_draft(session, story_draft=story_draft, created_by_user_id=created_by_user_id)
    story_draft.title = version.title
    story_draft.full_text = version.full_text
    story_draft.summary = version.summary
    story_draft.review_status = version.review_status
    story_draft.review_notes = version.review_notes
    story_draft.approved_text = version.approved_text
    story_draft.updated_at = utc_now()
    session.add(story_draft)
    session.commit()
    session.refresh(story_draft)
    return story_draft


def rollback_story_page(
    session: Session,
    *,
    story_page: StoryPage,
    version: StoryPageVersion,
    created_by_user_id: int | None = None,
) -> StoryPage:
    if version.story_page_id != story_page.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version does not belong to this story page")
    if version.page_number != story_page.page_number:
        existing = session.exec(
            select(StoryPage).where(
                StoryPage.story_draft_id == story_page.story_draft_id,
                StoryPage.page_number == version.page_number,
            )
        ).first()
        if existing is not None and existing.id != story_page.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot rollback because another page already uses that page number",
            )
    snapshot_story_page(session, story_page=story_page, created_by_user_id=created_by_user_id)
    story_page.page_number = version.page_number
    story_page.page_text = version.page_text
    story_page.scene_summary = version.scene_summary
    story_page.location = version.location
    story_page.mood = version.mood
    story_page.characters_present = version.characters_present
    story_page.illustration_prompt = version.illustration_prompt
    story_page.image_url = version.image_url
    story_page.updated_at = utc_now()
    session.add(story_page)
    session.commit()
    session.refresh(story_page)
    return story_page
