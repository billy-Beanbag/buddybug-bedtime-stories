from collections.abc import Callable
from typing import TypeVar

from sqlmodel import Session, select  # noqa: F401 - select used in delete_workflow_record

from app.models import AutomationSchedule, Book, BookAudio, Illustration, StoryDraft, StoryIdea, StoryPage, StorySuggestion, WorkflowJob
from app.services.review_service import utc_now
from app.schemas.admin_schema import AdminIllustrationSummary, AdminNextActionItem, PipelineCountsResponse

TActionEntity = TypeVar("TActionEntity")


def _count_rows(session: Session, statement) -> int:
    return len(list(session.exec(statement).all()))


def get_pipeline_counts(session: Session) -> PipelineCountsResponse:
    return PipelineCountsResponse(
        idea_pending=_count_rows(session, select(StoryIdea).where(StoryIdea.status == "idea_pending")),
        idea_selected=_count_rows(session, select(StoryIdea).where(StoryIdea.status == "idea_selected")),
        draft_pending_review=_count_rows(
            session, select(StoryDraft).where(StoryDraft.review_status == "draft_pending_review")
        ),
        needs_revision=_count_rows(session, select(StoryDraft).where(StoryDraft.review_status == "needs_revision")),
        approved_for_illustration=_count_rows(
            session, select(StoryDraft).where(StoryDraft.review_status == "approved_for_illustration")
        ),
        story_pages_prompt_ready=_count_rows(
            session, select(StoryPage).where(StoryPage.image_status == "prompt_ready")
        ),
        story_pages_image_generated=_count_rows(
            session, select(StoryPage).where(StoryPage.image_status == "image_generated")
        ),
        story_pages_image_approved=_count_rows(
            session, select(StoryPage).where(StoryPage.image_status == "image_approved")
        ),
        story_pages_image_rejected=_count_rows(
            session, select(StoryPage).where(StoryPage.image_status == "image_rejected")
        ),
        illustrations_generated=_count_rows(
            session, select(Illustration).where(Illustration.approval_status == "generated")
        ),
        illustrations_approved=_count_rows(
            session, select(Illustration).where(Illustration.approval_status == "approved")
        ),
        illustrations_rejected=_count_rows(
            session, select(Illustration).where(Illustration.approval_status == "rejected")
        ),
        books_ready=_count_rows(session, select(Book).where(Book.publication_status == "ready")),
        books_published=_count_rows(session, select(Book).where(Book.publication_status == "published")),
        audio_generated=_count_rows(session, select(BookAudio).where(BookAudio.approval_status == "generated")),
        audio_approved=_count_rows(session, select(BookAudio).where(BookAudio.approval_status == "approved")),
        audio_rejected=_count_rows(session, select(BookAudio).where(BookAudio.approval_status == "rejected")),
        workflow_jobs_queued=_count_rows(session, select(WorkflowJob).where(WorkflowJob.status == "queued")),
        workflow_jobs_running=_count_rows(session, select(WorkflowJob).where(WorkflowJob.status == "running")),
        workflow_jobs_failed=_count_rows(session, select(WorkflowJob).where(WorkflowJob.status == "failed")),
        automation_schedules_active=_count_rows(
            session, select(AutomationSchedule).where(AutomationSchedule.is_active == True)  # noqa: E712
        ),
        automation_schedules_due=_count_rows(
            session,
            select(AutomationSchedule).where(
                AutomationSchedule.is_active == True,  # noqa: E712
                AutomationSchedule.next_run_at != None,  # noqa: E711
                AutomationSchedule.next_run_at <= utc_now(),
            ),
        ),
    )


def delete_workflow_record(
    session: Session,
    *,
    book_id: int | None = None,
    draft_id: int | None = None,
    idea_id: int | None = None,
) -> None:
    """Delete a workflow record (book, draft, idea) and all dependencies in correct order."""
    from app.models import (
        AnalyticsEvent,
        BedtimePackItem,
        Book,
        BookAudio,
        BookCollectionItem,
        BookDiscoveryMetadata,
        BookDownloadPackage,
        BookNarration,
        BookPage,
        BookPageTranslation,
        BookTranslation,
        ClassroomSetItem,
        DailyStorySuggestion,
        Illustration,
        IllustrationQualityReview,
        NarrationSegment,
        ReadingPlanSession,
        ReadingProgress,
        ReadAlongSession,
        ReengagementSuggestion,
        SeasonalCampaignItem,
        StoryBrief,
        StoryDraft,
        StoryDraftVersion,
        StoryIdea,
        StoryPage,
        StoryPageVersion,
        StoryQualityReview,
        StorySuggestion,
        StoryReviewQueue,
        SupportTicket,
        TranslationTask,
        UserLibraryItem,
        UserStoryFeedback,
    )

    if book_id is not None:
        book = session.get(Book, book_id)
        if book is not None:
            # Delete BookPageTranslations first (reference BookPage)
            for page in session.exec(select(BookPage).where(BookPage.book_id == book_id)).all():
                for t in session.exec(
                    select(BookPageTranslation).where(BookPageTranslation.book_page_id == page.id)
                ).all():
                    session.delete(t)
            for page in session.exec(select(BookPage).where(BookPage.book_id == book_id)).all():
                session.delete(page)
            for m in session.exec(select(BookDiscoveryMetadata).where(BookDiscoveryMetadata.book_id == book_id)).all():
                session.delete(m)
            for a in session.exec(select(BookAudio).where(BookAudio.book_id == book_id)).all():
                session.delete(a)
            for n in session.exec(select(BookNarration).where(BookNarration.book_id == book_id)).all():
                for seg in session.exec(
                    select(NarrationSegment).where(NarrationSegment.narration_id == n.id)
                ).all():
                    session.delete(seg)
                session.delete(n)
            for t in session.exec(select(BookTranslation).where(BookTranslation.book_id == book_id)).all():
                session.delete(t)
            for u in session.exec(select(UserLibraryItem).where(UserLibraryItem.book_id == book_id)).all():
                session.delete(u)
            for c in session.exec(select(BookCollectionItem).where(BookCollectionItem.book_id == book_id)).all():
                session.delete(c)
            for d in session.exec(select(BookDownloadPackage).where(BookDownloadPackage.book_id == book_id)).all():
                session.delete(d)
            for r in session.exec(select(ReadingProgress).where(ReadingProgress.book_id == book_id)).all():
                session.delete(r)
            for r in session.exec(select(ReadAlongSession).where(ReadAlongSession.book_id == book_id)).all():
                session.delete(r)
            for d in session.exec(select(DailyStorySuggestion).where(DailyStorySuggestion.book_id == book_id)).all():
                session.delete(d)
            for b in session.exec(select(BedtimePackItem).where(BedtimePackItem.book_id == book_id)).all():
                session.delete(b)
            for s in session.exec(select(SeasonalCampaignItem).where(SeasonalCampaignItem.book_id == book_id)).all():
                session.delete(s)
            for c in session.exec(select(ClassroomSetItem).where(ClassroomSetItem.book_id == book_id)).all():
                session.delete(c)
            for t in session.exec(select(TranslationTask).where(TranslationTask.book_id == book_id)).all():
                session.delete(t)
            for f in session.exec(select(UserStoryFeedback).where(UserStoryFeedback.book_id == book_id)).all():
                session.delete(f)
            for s in session.exec(select(SupportTicket).where(SupportTicket.related_book_id == book_id)).all():
                s.related_book_id = None
            for r in session.exec(select(ReengagementSuggestion).where(ReengagementSuggestion.related_book_id == book_id)).all():
                r.related_book_id = None
            for a in session.exec(select(AnalyticsEvent).where(AnalyticsEvent.book_id == book_id)).all():
                a.book_id = None
            for r in session.exec(select(ReadingPlanSession).where(ReadingPlanSession.suggested_book_id == book_id)).all():
                r.suggested_book_id = None
            session.delete(book)
            session.commit()

    if draft_id is not None:
        draft = session.get(StoryDraft, draft_id)
        if draft is not None:
            # Delete books (and their dependencies) that reference this draft first
            for book in session.exec(select(Book).where(Book.story_draft_id == draft_id)).all():
                delete_workflow_record(session, book_id=book.id)
            page_ids = [p.id for p in session.exec(select(StoryPage).where(StoryPage.story_draft_id == draft_id)).all()]
            for pid in page_ids:
                for ill in session.exec(select(Illustration).where(Illustration.story_page_id == pid)).all():
                    for r in session.exec(
                        select(IllustrationQualityReview).where(IllustrationQualityReview.illustration_id == ill.id)
                    ).all():
                        session.delete(r)
                    session.delete(ill)
                for v in session.exec(select(StoryPageVersion).where(StoryPageVersion.story_page_id == pid)).all():
                    session.delete(v)
            for page in session.exec(select(StoryPage).where(StoryPage.story_draft_id == draft_id)).all():
                session.delete(page)
            for v in session.exec(select(StoryDraftVersion).where(StoryDraftVersion.story_draft_id == draft_id)).all():
                session.delete(v)
            for r in session.exec(select(StoryReviewQueue).where(StoryReviewQueue.story_id == draft_id)).all():
                session.delete(r)
            for q in session.exec(select(StoryQualityReview).where(StoryQualityReview.story_id == draft_id)).all():
                session.delete(q)
            for q in session.exec(select(IllustrationQualityReview).where(IllustrationQualityReview.story_id == draft_id)).all():
                session.delete(q)
            session.delete(draft)
            session.commit()

    if idea_id is not None:
        idea = session.get(StoryIdea, idea_id)
        if idea is not None:
            for suggestion in session.exec(
                select(StorySuggestion).where(StorySuggestion.promoted_story_idea_id == idea_id)
            ).all():
                suggestion.promoted_story_idea_id = None
                suggestion.updated_at = utc_now()
                session.add(suggestion)
            for b in session.exec(select(StoryBrief).where(StoryBrief.story_idea_id == idea_id)).all():
                session.delete(b)
            session.delete(idea)
            session.commit()


def get_idea_queue(
    session: Session,
    *,
    status: str | None,
    limit: int,
) -> list[StoryIdea]:
    statement = select(StoryIdea).order_by(StoryIdea.created_at.desc()).limit(limit)
    if status and status.strip():
        statement = statement.where(StoryIdea.status == status)
    return list(session.exec(statement).all())


def get_draft_review_queue(
    session: Session,
    *,
    review_status: str | None,
    limit: int,
) -> list[StoryDraft]:
    statement = select(StoryDraft).order_by(StoryDraft.updated_at.asc()).limit(limit)
    if review_status:
        statement = statement.where(StoryDraft.review_status == review_status)
    else:
        statement = statement.where(
            (StoryDraft.review_status == "draft_pending_review")
            | (StoryDraft.review_status == "review_pending")
            | (StoryDraft.review_status == "needs_revision")
        )
    return list(session.exec(statement).all())


def get_approved_drafts_ready_for_planning(session: Session, *, limit: int) -> list[StoryDraft]:
    drafts = list(
        session.exec(
            select(StoryDraft)
            .where(StoryDraft.review_status == "approved_for_illustration")
            .order_by(StoryDraft.updated_at.asc())
        ).all()
    )
    ready_drafts: list[StoryDraft] = []
    for draft in drafts:
        existing_page = session.exec(select(StoryPage).where(StoryPage.story_draft_id == draft.id)).first()
        if existing_page is None:
            ready_drafts.append(draft)
        if len(ready_drafts) >= limit:
            break
    return ready_drafts


def get_story_pages_needing_images(
    session: Session,
    *,
    image_status: str | None,
    limit: int,
) -> list[StoryPage]:
    statement = select(StoryPage).order_by(StoryPage.updated_at.asc()).limit(limit)
    if image_status:
        statement = statement.where(StoryPage.image_status == image_status)
    else:
        statement = statement.where(StoryPage.image_status == "prompt_ready")
    return list(session.exec(statement).all())


def get_illustrations_awaiting_approval(
    session: Session,
    *,
    approval_status: str | None,
    limit: int,
) -> list[AdminIllustrationSummary]:
    statement = select(Illustration).order_by(Illustration.updated_at.asc()).limit(limit)
    if approval_status:
        statement = statement.where(Illustration.approval_status == approval_status)
    else:
        statement = statement.where(Illustration.approval_status == "generated")
    illustrations = list(session.exec(statement).all())
    summaries: list[AdminIllustrationSummary] = []
    for illustration in illustrations:
        story_page = session.get(StoryPage, illustration.story_page_id)
        story_draft = session.get(StoryDraft, story_page.story_draft_id) if story_page is not None else None
        book = (
            session.exec(select(Book).where(Book.story_draft_id == story_draft.id).order_by(Book.updated_at.desc())).first()
            if story_draft is not None
            else None
        )
        summaries.append(
            AdminIllustrationSummary(
                id=illustration.id,
                story_page_id=illustration.story_page_id,
                story_draft_id=story_page.story_draft_id if story_page is not None else None,
                story_draft_title=story_draft.title if story_draft is not None else None,
                book_id=book.id if book is not None else None,
                page_number=story_page.page_number if story_page is not None else None,
                scene_summary=story_page.scene_summary if story_page is not None else None,
                approval_status=illustration.approval_status,
                provider=illustration.provider,
                version_number=illustration.version_number,
                image_url=illustration.image_url,
                created_at=illustration.created_at,
                updated_at=illustration.updated_at,
            )
        )
    return summaries


def get_books_ready_or_unpublished(
    session: Session,
    *,
    publication_status: str | None,
    published: bool | None,
    limit: int,
) -> list[Book]:
    statement = select(Book).order_by(Book.updated_at.asc()).limit(limit)
    if publication_status:
        statement = statement.where(Book.publication_status == publication_status)
    if published is not None:
        statement = statement.where(Book.published == published)
    return list(session.exec(statement).all())


def get_audio_awaiting_approval(
    session: Session,
    *,
    approval_status: str | None,
    limit: int,
) -> list[BookAudio]:
    statement = select(BookAudio).order_by(BookAudio.updated_at.asc()).limit(limit)
    if approval_status:
        statement = statement.where(BookAudio.approval_status == approval_status)
    else:
        statement = statement.where(BookAudio.approval_status == "generated")
    return list(session.exec(statement).all())


def _draft_title_getter(_: Session, draft: StoryDraft) -> str:
    return draft.title


def _story_page_title_getter(session: Session, page: StoryPage) -> str:
    draft = session.get(StoryDraft, page.story_draft_id)
    draft_title = draft.title if draft is not None else "Story draft"
    return f"{draft_title} - Page {page.page_number}"


def _illustration_title_getter(session: Session, illustration: Illustration) -> str:
    page = session.get(StoryPage, illustration.story_page_id)
    if page is None:
        return f"Illustration {illustration.id}"
    return _story_page_title_getter(session, page)


def _book_title_getter(_: Session, book: Book) -> str:
    return book.title


def _audio_title_getter(session: Session, audio: BookAudio) -> str:
    book = session.get(Book, audio.book_id)
    return book.title if book is not None else f"Book audio {audio.id}"


def _build_action_items(
    session: Session,
    *,
    items: list[TActionEntity],
    stage: str,
    entity_type: str,
    status_getter: Callable[[TActionEntity], str],
    suggested_action: str,
    title_getter: Callable[[Session, TActionEntity], str],
) -> list[AdminNextActionItem]:
    return [
        AdminNextActionItem(
            stage=stage,
            entity_type=entity_type,
            entity_id=item.id,
            title=title_getter(session, item),
            status=status_getter(item),
            suggested_action=suggested_action,
            created_at=item.created_at,
        )
        for item in items
    ]


def get_next_action_items(session: Session, *, limit: int) -> list[AdminNextActionItem]:
    actions: list[AdminNextActionItem] = []

    actions.extend(
        _build_action_items(
            session,
            items=get_draft_review_queue(session, review_status="draft_pending_review", limit=limit),
            stage="draft_review",
            entity_type="story_draft",
            status_getter=lambda draft: draft.review_status,
            suggested_action="Review draft",
            title_getter=_draft_title_getter,
        )
    )
    actions.extend(
        _build_action_items(
            session,
            items=get_draft_review_queue(session, review_status="needs_revision", limit=limit),
            stage="draft_revision",
            entity_type="story_draft",
            status_getter=lambda draft: draft.review_status,
            suggested_action="Revise draft",
            title_getter=_draft_title_getter,
        )
    )
    actions.extend(
        _build_action_items(
            session,
            items=get_approved_drafts_ready_for_planning(session, limit=limit),
            stage="illustration_planning",
            entity_type="story_draft",
            status_getter=lambda draft: draft.review_status,
            suggested_action="Generate illustration plan",
            title_getter=_draft_title_getter,
        )
    )
    actions.extend(
        _build_action_items(
            session,
            items=get_story_pages_needing_images(session, image_status="prompt_ready", limit=limit),
            stage="image_generation",
            entity_type="story_page",
            status_getter=lambda page: page.image_status,
            suggested_action="Generate illustration",
            title_getter=_story_page_title_getter,
        )
    )
    actions.extend(
        _build_action_items(
            session,
            items=get_illustrations_awaiting_approval(session, approval_status="generated", limit=limit),
            stage="illustration_review",
            entity_type="illustration",
            status_getter=lambda illustration: illustration.approval_status,
            suggested_action="Approve illustration",
            title_getter=_illustration_title_getter,
        )
    )
    actions.extend(
        _build_action_items(
            session,
            items=get_books_ready_or_unpublished(
                session, publication_status="ready", published=False, limit=limit
            ),
            stage="book_publication",
            entity_type="book",
            status_getter=lambda book: book.publication_status,
            suggested_action="Publish book",
            title_getter=_book_title_getter,
        )
    )
    actions.extend(
        _build_action_items(
            session,
            items=get_audio_awaiting_approval(session, approval_status="generated", limit=limit),
            stage="audio_review",
            entity_type="book_audio",
            status_getter=lambda audio: audio.approval_status,
            suggested_action="Approve audio",
            title_getter=_audio_title_getter,
        )
    )

    actions.sort(key=lambda item: item.created_at)
    return actions[:limit]
