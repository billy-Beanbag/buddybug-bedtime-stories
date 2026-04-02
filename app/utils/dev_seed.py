from dataclasses import dataclass

from sqlmodel import Session, select

from app.models import Book, BookAudio, BookPage, Illustration, ReadingProgress, StoryDraft, StoryIdea, StoryPage, User
from app.services.audio_service import approve_book_audio, generate_book_audio, list_available_voices
from app.services.book_builder import assemble_book_from_draft
from app.services.feedback_service import create_or_update_feedback, rebuild_user_story_profile
from app.services.idea_generator import CANONICAL_CHARACTER_ORDER, generate_story_idea_payloads
from app.services.i18n_service import upsert_book_page_translation, upsert_book_translation
from app.services.illustration_generator import approve_illustration, generate_mock_illustration
from app.services.illustration_planner import generate_story_page_payloads
from app.services.narration_service import generate_book_narration
from app.services.review_service import approve_story_draft, utc_now
from app.services.story_writer import generate_story_draft_payload
from app.utils.auth import hash_password
from app.utils.seed_characters import seed_characters
from app.utils.seed_content_lanes import seed_content_lanes
from app.utils.seed_voices import seed_voices


DEMO_ADMIN_EMAIL = "admin@buddybug.local"
DEMO_ADMIN_PASSWORD = "Admin123!"
DEMO_PREMIUM_EMAIL = "premium@buddybug.local"
DEMO_PREMIUM_PASSWORD = "Premium123!"
DEMO_FREE_EMAIL = "free@buddybug.local"
DEMO_FREE_PASSWORD = "Free123!"


@dataclass
class DemoSeedResult:
    admin_user: User
    premium_user: User
    free_user: User
    story_ideas: list[StoryIdea]
    story_draft: StoryDraft
    story_pages: list[StoryPage]
    illustrations: list[Illustration]
    book: Book
    audio: BookAudio | None


def _get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return session.exec(statement).first()


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def ensure_demo_user(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    is_admin: bool,
    subscription_tier: str,
    subscription_status: str,
) -> User:
    user = _get_user_by_email(session, email)
    if user is None:
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name=display_name,
            is_admin=is_admin,
            is_editor=is_admin,
            subscription_tier=subscription_tier,
            subscription_status=subscription_status,
        )
    else:
        user.password_hash = hash_password(password)
        user.display_name = display_name
        user.is_admin = is_admin
        user.is_editor = is_admin
        user.subscription_tier = subscription_tier
        user.subscription_status = subscription_status
        user.is_active = True
        user.updated_at = utc_now()
    return _persist(session, user)


def ensure_demo_story_ideas(session: Session) -> list[StoryIdea]:
    batch = generate_story_idea_payloads(
        count=2,
        age_band="3-7",
        content_lane_key=None,
        tone="calming, dreamy, gentle",
        include_characters=CANONICAL_CHARACTER_ORDER[:4],
        bedtime_only=True,
        available_characters=CANONICAL_CHARACTER_ORDER,
    )

    ideas: list[StoryIdea] = []
    for payload in batch.payloads:
        existing = session.exec(select(StoryIdea).where(StoryIdea.title == payload["title"])).first()
        if existing is None:
            existing = StoryIdea(**payload)
            session.add(existing)
            session.commit()
            session.refresh(existing)
        ideas.append(existing)
    return ideas


def ensure_demo_story_draft(session: Session, story_idea: StoryIdea) -> StoryDraft:
    existing = session.exec(select(StoryDraft).where(StoryDraft.story_idea_id == story_idea.id)).first()
    if existing is None:
        payload = generate_story_draft_payload(story_idea)
        existing = StoryDraft(
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
        session.add(existing)
        story_idea.status = "converted_to_draft"
        story_idea.updated_at = utc_now()
        session.add(story_idea)
        session.commit()
        session.refresh(existing)

    if existing.review_status != "approved_for_illustration":
        existing = approve_story_draft(session, existing)
    return existing


def ensure_story_pages(session: Session, story_draft: StoryDraft, story_idea: StoryIdea) -> list[StoryPage]:
    existing_pages = list(
        session.exec(
            select(StoryPage)
            .where(StoryPage.story_draft_id == story_draft.id)
            .order_by(StoryPage.page_number)
        ).all()
    )
    if existing_pages:
        return existing_pages

    payloads = generate_story_page_payloads(
        story_draft=story_draft,
        story_idea=story_idea,
        target_page_count=8,
        min_pages=5,
        max_pages=6,
    )
    pages: list[StoryPage] = []
    for payload in payloads:
        page = StoryPage(**payload)
        session.add(page)
        pages.append(page)
    session.commit()
    for page in pages:
        session.refresh(page)
    return pages


def ensure_illustrations(session: Session, story_pages: list[StoryPage]) -> list[Illustration]:
    created: list[Illustration] = []
    for page in story_pages:
        approved = session.exec(
            select(Illustration)
            .where(Illustration.story_page_id == page.id, Illustration.approval_status == "approved")
            .order_by(Illustration.version_number.desc())
        ).first()
        if approved is None:
            generated = generate_mock_illustration(session, story_page=page, generation_notes="Demo seed illustration")
            approved = approve_illustration(session, generated)
        created.append(approved)
    return created


def ensure_demo_book(session: Session, story_draft: StoryDraft) -> Book:
    existing = session.exec(select(Book).where(Book.story_draft_id == story_draft.id)).first()
    if existing is None:
        existing, _ = assemble_book_from_draft(
            session,
            story_draft_id=story_draft.id,
            language="en",
            content_lane_key=story_draft.content_lane_key,
            publish_immediately=True,
            replace_existing=True,
        )
    elif not existing.published or existing.publication_status != "published":
        existing.published = True
        existing.publication_status = "published"
        existing.updated_at = utc_now()
        existing = _persist(session, existing)
    return existing


def ensure_demo_audio(session: Session, book: Book) -> BookAudio | None:
    existing = session.exec(
        select(BookAudio)
        .where(BookAudio.book_id == book.id, BookAudio.approval_status == "approved")
        .order_by(BookAudio.version_number.desc())
    ).first()
    if existing is not None:
        return existing

    voices = list_available_voices(session, language="en", is_active=True)
    if not voices:
        return None

    audio = generate_book_audio(
        session,
        book_id=book.id,
        voice_id=voices[0].id,
        script_source="assembled_book_text",
        generation_notes="Demo seed audio",
        replace_active_for_voice=True,
    )
    return approve_book_audio(
        session,
        audio=audio,
        generation_notes="Approved demo audio",
        make_active=True,
    )


def ensure_demo_narration(session: Session, book: Book) -> None:
    voices = list_available_voices(session, language="en", is_active=True)
    if not voices:
        return
    generate_book_narration(
        session,
        book_id=book.id,
        voice_key=voices[0].key,
        language="en",
        replace_existing=False,
        actor_user=None,
    )


def ensure_demo_translations(session: Session, book: Book) -> None:
    pages = list(session.exec(select(BookPage).where(BookPage.book_id == book.id).order_by(BookPage.page_number)).all())
    if not pages:
        return

    upsert_book_translation(
        session,
        book_id=book.id,
        language="es",
        title="La luz de cuentos de Buddybug",
        description="Edicion de demostracion en espanol para pruebas de localizacion.",
        published=True,
    )
    upsert_book_translation(
        session,
        book_id=book.id,
        language="fr",
        title="La veilleuse d'histoires de Buddybug",
        description="Edition de demonstration en francais pour les tests de localisation.",
        published=True,
    )

    spanish_pages = {
        0: "Verity sonrio con calma mientras la hora de dormir llegaba suavemente y Buddybug encendia una pequena luz dorada para comenzar la historia.",
        1: "Dolly y Daphne escucharon en silencio mientras la habitacion se llenaba de brillo tranquilo, almohadas suaves y promesas de una aventura apacible.",
        2: "Muy pronto, el jardin de la noche parecio abrirse como un libro amable, y cada paso recordaba a los amigos que la calma tambien puede ser una aventura.",
    }
    french_pages = {
        0: "Verity sourit doucement pendant que l'heure du coucher arrivait et que Buddybug allumait une petite lueur doree pour commencer l'histoire.",
    }

    for page in pages:
        if page.page_number in spanish_pages:
            upsert_book_page_translation(
                session,
                book_page_id=page.id,
                language="es",
                text_content=spanish_pages[page.page_number],
            )
        if page.page_number in french_pages:
            upsert_book_page_translation(
                session,
                book_page_id=page.id,
                language="fr",
                text_content=french_pages[page.page_number],
            )


def ensure_demo_progress_and_feedback(session: Session, premium_user: User, book: Book) -> None:
    progress = session.exec(
        select(ReadingProgress).where(
            ReadingProgress.reader_identifier == premium_user.email,
            ReadingProgress.book_id == book.id,
        )
    ).first()
    if progress is None:
        progress = ReadingProgress(
            reader_identifier=premium_user.email,
            book_id=book.id,
            current_page_number=2,
            completed=False,
        )
    else:
        progress.current_page_number = 2
        progress.completed = False
        progress.last_opened_at = utc_now()
        progress.updated_at = utc_now()
    _persist(session, progress)

    create_or_update_feedback(
        session,
        user_id=premium_user.id,
        book_id=book.id,
        liked=True,
        rating=5,
        completed=True,
        replayed=False,
        preferred_character="Buddybug",
        preferred_style="soft watercolor",
        preferred_tone="calming",
        feedback_notes="Perfect for local demos.",
    )
    rebuild_user_story_profile(session, user_id=premium_user.id)


def seed_demo_environment(session: Session, *, include_audio: bool = True) -> DemoSeedResult:
    seed_characters(session)
    seed_content_lanes(session)
    seed_voices(session)

    admin_user = ensure_demo_user(
        session,
        email=DEMO_ADMIN_EMAIL,
        password=DEMO_ADMIN_PASSWORD,
        display_name="Buddybug Admin",
        is_admin=True,
        subscription_tier="premium",
        subscription_status="active",
    )
    premium_user = ensure_demo_user(
        session,
        email=DEMO_PREMIUM_EMAIL,
        password=DEMO_PREMIUM_PASSWORD,
        display_name="Premium Demo",
        is_admin=False,
        subscription_tier="premium",
        subscription_status="active",
    )
    free_user = ensure_demo_user(
        session,
        email=DEMO_FREE_EMAIL,
        password=DEMO_FREE_PASSWORD,
        display_name="Free Demo",
        is_admin=False,
        subscription_tier="free",
        subscription_status="none",
    )

    story_ideas = ensure_demo_story_ideas(session)
    story_draft = ensure_demo_story_draft(session, story_ideas[0])
    story_pages = ensure_story_pages(session, story_draft, story_ideas[0])
    illustrations = ensure_illustrations(session, story_pages)
    book = ensure_demo_book(session, story_draft)
    audio = ensure_demo_audio(session, book) if include_audio else None
    if include_audio:
        ensure_demo_narration(session, book)
    ensure_demo_translations(session, book)
    ensure_demo_progress_and_feedback(session, premium_user, book)

    return DemoSeedResult(
        admin_user=admin_user,
        premium_user=premium_user,
        free_user=free_user,
        story_ideas=story_ideas,
        story_draft=story_draft,
        story_pages=story_pages,
        illustrations=illustrations,
        book=book,
        audio=audio,
    )
