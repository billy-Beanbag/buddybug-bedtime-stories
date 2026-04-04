from sqlmodel import Session

from app.models import StoryDraft, StoryIdea, User
from app.services.audio_service import approve_book_audio, generate_book_audio, list_available_voices
from app.services.book_builder import assemble_book_from_draft
from app.services.idea_generator import CANONICAL_CHARACTER_ORDER, generate_story_idea_payloads
from app.services.illustration_generator import approve_illustration, generate_mock_illustration
from app.services.illustration_planner import generate_story_page_payloads
from app.services.review_service import approve_story_draft
from app.services.story_writer import generate_story_draft_payload
from app.utils.auth import create_access_token, hash_password


def create_test_user(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    is_admin: bool = False,
    is_editor: bool = False,
    is_educator: bool = False,
    subscription_tier: str = "free",
    subscription_status: str = "none",
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        is_admin=is_admin,
        is_editor=is_editor,
        is_educator=is_educator,
        subscription_tier=subscription_tier,
        subscription_status=subscription_status,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def make_auth_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": user.email, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}


def create_story_idea(session: Session, *, index: int = 0) -> StoryIdea:
    payload = generate_story_idea_payloads(
        count=index + 1,
        age_band="3-7",
        content_lane_key=None,
        tone="calm, gentle, plot-led",
        include_characters=None,
        bedtime_only=True,
        available_characters=CANONICAL_CHARACTER_ORDER,
    ).payloads[index]
    story_idea = StoryIdea(**payload)
    session.add(story_idea)
    session.commit()
    session.refresh(story_idea)
    return story_idea


def create_story_idea_for_lane(
    session: Session,
    *,
    age_band: str,
    content_lane_key: str | None = None,
    index: int = 0,
) -> StoryIdea:
    payload = generate_story_idea_payloads(
        count=index + 1,
        age_band=age_band,
        content_lane_key=content_lane_key,
        tone="calm, gentle, plot-led" if age_band == "3-7" else "warm, adventurous, plot-led",
        include_characters=None,
        bedtime_only=age_band == "3-7",
        available_characters=CANONICAL_CHARACTER_ORDER,
    ).payloads[index]
    story_idea = StoryIdea(**payload)
    session.add(story_idea)
    session.commit()
    session.refresh(story_idea)
    return story_idea


def create_approved_draft(session: Session, *, idea_index: int = 0) -> StoryDraft:
    story_idea = create_story_idea(session, index=idea_index)
    payload = generate_story_draft_payload(story_idea)
    story_draft = StoryDraft(
        story_idea_id=story_idea.id,
        title=payload.title,
        age_band=story_idea.age_band,
        language="en",
        content_lane_key=payload.content_lane_key,
        full_text=payload.full_text,
        summary=payload.summary,
        read_time_minutes=payload.read_time_minutes,
        review_status=payload.review_status,
        generation_source=payload.generation_source,
    )
    session.add(story_draft)
    story_idea.status = "converted_to_draft"
    session.add(story_idea)
    session.commit()
    session.refresh(story_draft)
    return approve_story_draft(session, story_draft)


def create_demo_pipeline(
    session: Session,
    *,
    publish: bool = True,
    with_audio: bool = True,
    idea_index: int = 0,
    language: str = "en",
) -> dict[str, object]:
    story_draft = create_approved_draft(session, idea_index=idea_index)
    from app.models import StoryIdea

    story_idea = session.get(StoryIdea, story_draft.story_idea_id)
    page_payloads = generate_story_page_payloads(
        story_draft=story_draft,
        story_idea=story_idea,
        target_page_count=6,
        min_pages=5,
        max_pages=6,
    )

    story_pages = []
    for payload in page_payloads:
        from app.models import StoryPage

        page = StoryPage(**payload)
        session.add(page)
        story_pages.append(page)
    session.commit()
    for page in story_pages:
        session.refresh(page)

    illustrations = []
    for page in story_pages:
        illustration = generate_mock_illustration(session, story_page=page)
        illustration = approve_illustration(session, illustration)
        illustrations.append(illustration)

    book, book_pages = assemble_book_from_draft(
        session,
        story_draft_id=story_draft.id,
        language=language,
        content_lane_key=story_draft.content_lane_key,
        publish_immediately=publish,
        replace_existing=True,
    )

    audio = None
    if with_audio:
        voices = list_available_voices(session, language="en", is_active=True)
        if voices:
            audio = generate_book_audio(
                session,
                book_id=book.id,
                voice_id=voices[0].id,
                script_source="assembled_book_text",
                generation_notes="Automated test narration",
                replace_active_for_voice=True,
            )
            audio = approve_book_audio(
                session,
                audio=audio,
                generation_notes="Approved for tests",
                make_active=True,
            )

    return {
        "story_draft": story_draft,
        "story_pages": story_pages,
        "illustrations": illustrations,
        "book": book,
        "book_pages": book_pages,
        "audio": audio,
    }
