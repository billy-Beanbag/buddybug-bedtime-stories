import html
import logging

from fastapi import HTTPException, status
from sqlmodel import Session, desc, select

from app.models import Book, BookPage, Illustration, StoryDraft, StoryIdea, StoryPage
from app.services.illustration_generation_service import generate_live_image_from_prompt, has_live_illustration_provider_config
from app.services.storage_service import (
    build_generated_cover_path,
    build_mock_cover_path,
    get_asset_url,
    get_image_asset_validation_error,
    save_bytes,
)

ALLOWED_PUBLICATION_STATUSES = {"assembling", "ready", "published", "archived"}
ALLOWED_LAYOUT_TYPES = {"cover", "text_image", "text_only", "image_only"}
logger = logging.getLogger(__name__)


def get_book_or_404(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


def get_story_draft_or_404(session: Session, story_draft_id: int) -> StoryDraft:
    story_draft = session.get(StoryDraft, story_draft_id)
    if story_draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story draft not found")
    return story_draft


def validate_publication_status(publication_status: str) -> str:
    if publication_status not in ALLOWED_PUBLICATION_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid publication status")
    return publication_status


def determine_layout_type(text_content: str, image_url: str | None) -> str:
    has_text = bool(text_content.strip())
    has_image = bool(image_url)
    if has_text and has_image:
        return "text_image"
    if has_text:
        return "text_only"
    if has_image:
        return "image_only"
    return "text_only"


def get_best_image_for_story_page(session: Session, story_page: StoryPage) -> str | None:
    return get_best_release_image_for_story_page(session, story_page)


def get_best_release_image_for_story_page(session: Session, story_page: StoryPage) -> str | None:
    for approval_status in ("approved",):
        statement = (
            select(Illustration)
            .where(
                Illustration.story_page_id == story_page.id,
                Illustration.approval_status == approval_status,
            )
            .order_by(desc(Illustration.version_number), desc(Illustration.created_at))
        )
        for illustration in session.exec(statement).all():
            validation_error = get_image_asset_validation_error(illustration.image_url)
            if validation_error is None:
                return illustration.image_url
            logger.warning(
                "Skipping invalid %s illustration %s for story page %s: %s",
                approval_status,
                illustration.id,
                story_page.id,
                validation_error,
            )

    if story_page.image_status == "image_approved" and story_page.image_url:
        validation_error = get_image_asset_validation_error(story_page.image_url)
        if validation_error is None:
            return story_page.image_url
        logger.warning(
            "Skipping invalid story page image for story page %s: %s",
            story_page.id,
            validation_error,
        )
    return None


def build_cover_page(book_id: int, title: str, cover_image_url: str | None) -> BookPage:
    return BookPage(
        book_id=book_id,
        source_story_page_id=None,
        page_number=0,
        text_content=title,
        image_url=cover_image_url,
        layout_type="cover",
    )


def _split_character_names(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _story_cover_prompt(story_draft: StoryDraft, story_idea: StoryIdea | None, story_pages: list[StoryPage]) -> str:
    page_summaries = [(page.scene_summary or "").strip() for page in story_pages[:4] if (page.scene_summary or "").strip()]
    page_locations = [(page.location or "").strip() for page in story_pages[:4] if (page.location or "").strip()]
    characters = _ordered_unique(
        [
            *_split_character_names(story_idea.main_characters if story_idea is not None else None),
            *_split_character_names(story_idea.supporting_characters if story_idea is not None else None),
            *[
                item.strip()
                for page in story_pages[:4]
                for item in (page.characters_present or "").split(",")
                if item.strip()
            ],
        ]
    )
    summary = (story_draft.summary or (story_idea.premise if story_idea is not None else "")).strip()
    theme = (story_idea.theme if story_idea is not None else "").strip()
    tone = (story_idea.tone if story_idea is not None else "").strip()
    location = page_locations[0] if page_locations else "storybook bedtime setting"
    scene_overview = " | ".join(page_summaries[:3])
    character_line = ", ".join(characters[:5]) if characters else "Buddybug bedtime story characters"

    return "\n".join(
        [
            f"Create a premium landscape storybook cover illustration for the children's book titled '{story_draft.title}'.",
            "Use a wide, cinematic composition that works as a cover image, not an inside page.",
            f"Story summary: {summary or 'Gentle bedtime adventure with a calm emotional arc.'}",
            f"Main characters to feature clearly: {character_line}.",
            f"Primary setting: {location}.",
            f"Story tone: {tone or 'calm, gentle, comforting'}." if tone else "Story tone: calm, gentle, comforting.",
            f"Theme: {theme}." if theme else "Theme: friendship, reassurance, bedtime calm.",
            f"Key visual beats to hint at across the cover: {scene_overview}." if scene_overview else "",
            "Show an overview of the whole story world with the cast together in one coherent scene.",
            "Keep the image suitable for ages 3-7, warm, magical, polished, and emotionally readable.",
            "Use a cinematic landscape cover composition with strong silhouettes and clear faces.",
            "Do not render any title text, captions, lettering, logos, or watermarks inside the artwork.",
        ]
    ).strip()


def _build_mock_cover_svg(title: str, summary: str, characters: str) -> bytes:
    escaped_title = html.escape(title)
    escaped_summary = html.escape(summary[:180] or "Standalone landscape cover preview")
    escaped_characters = html.escape(characters[:180] or "Buddybug story cast")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024" viewBox="0 0 1536 1024" fill="none">
  <defs>
    <linearGradient id="coverSky" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#172554" />
      <stop offset="50%" stop-color="#4338CA" />
      <stop offset="100%" stop-color="#A855F7" />
    </linearGradient>
    <radialGradient id="coverGlow" cx="0" cy="0" r="1" gradientTransform="translate(1110 240) rotate(90) scale(320 320)">
      <stop offset="0%" stop-color="#FEF3C7" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#FEF3C7" stop-opacity="0" />
    </radialGradient>
  </defs>
  <rect width="1536" height="1024" rx="56" fill="url(#coverSky)" />
  <rect width="1536" height="1024" rx="56" fill="url(#coverGlow)" />
  <circle cx="1120" cy="220" r="112" fill="#F8FAFC" fill-opacity="0.92" />
  <rect x="72" y="72" width="1392" height="880" rx="40" fill="#0F172A" fill-opacity="0.18" stroke="#FFFFFF" stroke-opacity="0.24" />
  <text x="112" y="142" fill="#F8FAFC" font-family="Arial, sans-serif" font-size="30" letter-spacing="8">BUDDYBUG COVER PREVIEW</text>
  <text x="112" y="250" fill="#FFFFFF" font-family="Arial, sans-serif" font-size="74" font-weight="700">{escaped_title}</text>
  <text x="112" y="328" fill="#E2E8F0" font-family="Arial, sans-serif" font-size="30">{escaped_summary}</text>
  <rect x="112" y="392" width="1312" height="2" fill="#FFFFFF" fill-opacity="0.2" />
  <rect x="112" y="438" width="1312" height="300" rx="32" fill="#0F172A" fill-opacity="0.24" stroke="#FFFFFF" stroke-opacity="0.12" />
  <text x="152" y="508" fill="#F8FAFC" font-family="Arial, sans-serif" font-size="34" font-weight="700">Landscape cover artwork</text>
  <text x="152" y="570" fill="#E2E8F0" font-family="Arial, sans-serif" font-size="28">Characters: {escaped_characters}</text>
  <text x="152" y="632" fill="#CBD5E1" font-family="Arial, sans-serif" font-size="26">This standalone cover is generated separately from page 1 so the composition can represent the whole story.</text>
  <text x="152" y="694" fill="#CBD5E1" font-family="Arial, sans-serif" font-size="26">It is intended for a wide story overview instead of a portrait interior scene crop.</text>
</svg>"""
    return svg.encode("utf-8")


def _build_cover_image(
    *,
    story_draft: StoryDraft,
    story_idea: StoryIdea | None,
    story_pages: list[StoryPage],
    draft_page_images: dict[int, str | None],
    version_number: int,
) -> str | None:
    prompt = _story_cover_prompt(story_draft, story_idea, story_pages)
    reference_image_urls = [image_url for image_url in draft_page_images.values() if image_url][:4]
    if has_live_illustration_provider_config():
        try:
            live_result = generate_live_image_from_prompt(
                prompt=prompt,
                reference_image_urls=reference_image_urls,
                size="1536x1024",
                debug_context=f"book_cover:{story_draft.id}",
            )
            asset_path = build_generated_cover_path(
                story_draft_id=story_draft.id,
                version_number=version_number,
                extension=live_result.file_extension,
            )
            save_bytes(asset_path, live_result.image_bytes)
            image_url = get_asset_url(asset_path)
            validation_error = get_image_asset_validation_error(image_url)
            if validation_error is None:
                return image_url
            logger.warning("Discarding invalid generated cover for draft %s: %s", story_draft.id, validation_error)
        except Exception as exc:
            logger.warning("Falling back to mock cover generation for draft %s: %s", story_draft.id, exc)

    summary = (story_draft.summary or (story_idea.premise if story_idea is not None else "")).strip()
    characters = ", ".join(
        _ordered_unique(
            [
                *_split_character_names(story_idea.main_characters if story_idea is not None else None),
                *_split_character_names(story_idea.supporting_characters if story_idea is not None else None),
            ]
        )
    )
    asset_path = build_mock_cover_path(story_draft_id=story_draft.id, version_number=version_number)
    save_bytes(asset_path, _build_mock_cover_svg(story_draft.title, summary, characters))
    return get_asset_url(asset_path)


def _delete_book_with_pages(session: Session, book: Book) -> None:
    pages = session.exec(select(BookPage).where(BookPage.book_id == book.id)).all()
    for page in pages:
        session.delete(page)
    session.delete(book)


def _load_story_pages_or_400(session: Session, story_draft_id: int) -> list[StoryPage]:
    pages = list(
        session.exec(
            select(StoryPage)
            .where(StoryPage.story_draft_id == story_draft_id)
            .order_by(StoryPage.page_number)
        ).all()
    )
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story pages must exist before assembling a book",
        )
    return pages


def validate_story_pages_ready_for_release(
    session: Session,
    *,
    story_pages: list[StoryPage],
) -> None:
    missing_text_pages: list[int] = []
    incomplete_image_pages: list[int] = []
    non_contiguous_pages: list[int] = []

    expected_page_number = 1
    for page in story_pages:
        if page.page_number != expected_page_number:
            non_contiguous_pages.append(page.page_number)
        expected_page_number += 1

        if not (page.page_text or "").strip():
            missing_text_pages.append(page.page_number)

        if get_best_release_image_for_story_page(session, page) is None:
            incomplete_image_pages.append(page.page_number)

    if non_contiguous_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story pages must be contiguous starting at page 1 before book assembly",
        )
    if missing_text_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Story pages missing text: {', '.join(str(page) for page in missing_text_pages)}",
        )
    if incomplete_image_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "All story pages must have approved illustrations before book assembly. "
                f"Missing approved images for pages: {', '.join(str(page) for page in incomplete_image_pages)}"
            ),
        )


def assemble_book_from_draft(
    session: Session,
    *,
    story_draft_id: int,
    language: str,
    content_lane_key: str | None,
    publish_immediately: bool,
    replace_existing: bool,
) -> tuple[Book, list[BookPage]]:
    """Assemble a fresh Book from an approved draft and replace older books if requested."""
    story_draft = get_story_draft_or_404(session, story_draft_id)
    if story_draft.review_status != "approved_for_illustration":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story draft must be approved_for_illustration before book assembly",
        )

    source_text = (story_draft.approved_text or story_draft.full_text).strip()
    if not source_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Story draft must contain text before book assembly",
        )

    story_pages = _load_story_pages_or_400(session, story_draft_id)
    validate_story_pages_ready_for_release(session, story_pages=story_pages)

    existing_books = list(session.exec(select(Book).where(Book.story_draft_id == story_draft_id)).all())
    if existing_books and not replace_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A book already exists for this story draft",
        )
    for existing_book in existing_books:
        _delete_book_with_pages(session, existing_book)
    if existing_books:
        session.commit()

    story_idea = session.get(StoryIdea, story_draft.story_idea_id) if story_draft.story_idea_id is not None else None
    age_band = story_draft.age_band or (story_idea.age_band if story_idea is not None else "3-7")
    resolved_content_lane_key = (
        content_lane_key
        or story_draft.content_lane_key
        or (story_idea.content_lane_key if story_idea is not None else "bedtime_3_7")
    )
    publication_status = "published" if publish_immediately else "ready"

    draft_page_images = {page.id: get_best_release_image_for_story_page(session, page) for page in story_pages}
    cover_image_url = _build_cover_image(
        story_draft=story_draft,
        story_idea=story_idea,
        story_pages=story_pages,
        draft_page_images=draft_page_images,
        version_number=max(len(existing_books) + 1, 1),
    )

    book = Book(
        story_draft_id=story_draft.id,
        title=story_draft.title,
        cover_image_url=cover_image_url,
        age_band=age_band,
        content_lane_key=resolved_content_lane_key,
        language=language or story_draft.language,
        published=publish_immediately,
        publication_status=publication_status,
        audio_available=False,
    )
    session.add(book)
    session.commit()
    session.refresh(book)

    book_pages: list[BookPage] = [build_cover_page(book.id, book.title, book.cover_image_url)]
    for story_page in story_pages:
        image_url = draft_page_images.get(story_page.id)
        book_pages.append(
            BookPage(
                book_id=book.id,
                source_story_page_id=story_page.id,
                page_number=story_page.page_number,
                text_content=story_page.page_text,
                image_url=image_url,
                layout_type=determine_layout_type(story_page.page_text, image_url),
            )
        )

    for page in book_pages:
        session.add(page)
    session.commit()
    for page in book_pages:
        session.refresh(page)

    return book, book_pages
