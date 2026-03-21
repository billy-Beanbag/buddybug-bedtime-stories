import html

import httpx
from fastapi import HTTPException, status
from sqlmodel import Session, desc, select

from app.config import ILLUSTRATION_GENERATION_PROVIDER
from app.models import Illustration, StoryPage
from app.services.illustration_generation_service import (
    IllustrationGenerationPackage,
    build_illustration_generation_package,
    generate_live_illustration_image,
)
from app.services.review_service import utc_now
from app.services.storage_service import (
    build_generated_image_path,
    build_mock_image_path,
    get_asset_url,
    get_image_asset_validation_error,
    save_bytes,
)

ALLOWED_APPROVAL_STATUSES = {"generated", "approved", "rejected"}
ALLOWED_LIVE_PROVIDERS = {"future_ai_provider", "openai"}
ALLOWED_PROVIDERS = {"mock", "manual_upload", *ALLOWED_LIVE_PROVIDERS}


def _wrap_svg_lines(text: str, *, width: int, max_lines: int) -> list[str]:
    compact = " ".join(text.split())
    if not compact:
        return []
    lines: list[str] = []
    remaining = compact
    while remaining and len(lines) < max_lines:
        if len(remaining) <= width:
            lines.append(remaining)
            break
        split_at = remaining.rfind(" ", 0, width)
        if split_at <= 0:
            split_at = width
        lines.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining and lines:
        lines[-1] = f"{lines[-1][: max(width - 3, 1)].rstrip()}..."
    return lines


def _build_mock_illustration_svg(
    *,
    story_page: StoryPage,
    prompt_package: IllustrationGenerationPackage,
) -> bytes:
    escaped_title = html.escape(story_page.page_text[:120] or "Buddybug Story")
    page_label = f"Page {story_page.page_number}"
    summary_lines = [html.escape(line) for line in _wrap_svg_lines(prompt_package.scene_summary, width=56, max_lines=3)]
    character_lines = [html.escape(line) for line in _wrap_svg_lines(f"Characters: {prompt_package.characters_present or 'Story scene'}", width=56, max_lines=2)]
    context_lines = [
        html.escape(line)
        for line in _wrap_svg_lines(
            f"Location: {prompt_package.location}  Mood: {prompt_package.mood}",
            width=56,
            max_lines=2,
        )
    ]
    prompt_lines = [
        html.escape(line)
        for line in _wrap_svg_lines(prompt_package.positive_prompt or prompt_package.prompt_used, width=56, max_lines=4)
    ]

    detail_lines = [*summary_lines, *character_lines, *context_lines]
    detail_text = "\n".join(
        f'<text x="72" y="{352 + (index * 34)}" fill="#E2E8F0" font-family="Arial, sans-serif" '
        f'font-size="24">{line}</text>'
        for index, line in enumerate(detail_lines)
    )
    prompt_text = "\n".join(
        f'<text x="72" y="{642 + (index * 28)}" fill="#CBD5E1" font-family="Arial, sans-serif" '
        f'font-size="20">{line}</text>'
        for index, line in enumerate(prompt_lines)
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900" fill="none">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0F172A" />
      <stop offset="55%" stop-color="#1D4ED8" />
      <stop offset="100%" stop-color="#C084FC" />
    </linearGradient>
    <radialGradient id="glow" cx="0" cy="0" r="1" gradientTransform="translate(840 230) rotate(90) scale(280 280)">
      <stop offset="0%" stop-color="#FEF3C7" stop-opacity="0.9" />
      <stop offset="100%" stop-color="#FEF3C7" stop-opacity="0" />
    </radialGradient>
  </defs>
  <rect width="1200" height="900" rx="48" fill="url(#sky)" />
  <rect width="1200" height="900" rx="48" fill="url(#glow)" />
  <circle cx="890" cy="220" r="96" fill="#F8FAFC" fill-opacity="0.92" />
  <circle cx="320" cy="200" r="10" fill="#F8FAFC" fill-opacity="0.8" />
  <circle cx="380" cy="145" r="6" fill="#F8FAFC" fill-opacity="0.7" />
  <circle cx="430" cy="220" r="8" fill="#F8FAFC" fill-opacity="0.75" />
  <rect x="56" y="56" width="1088" height="788" rx="36" fill="#0F172A" fill-opacity="0.18" stroke="#FFFFFF" stroke-opacity="0.28" />
  <text x="72" y="112" fill="#F8FAFC" font-family="Arial, sans-serif" font-size="28" letter-spacing="6">BUDDYBUG STORYLIGHT</text>
  <text x="72" y="184" fill="#FFFFFF" font-family="Arial, sans-serif" font-size="58" font-weight="700">{html.escape(page_label)}</text>
  <text x="72" y="250" fill="#E2E8F0" font-family="Arial, sans-serif" font-size="28">{escaped_title}</text>
  <rect x="72" y="300" width="1056" height="2" fill="#FFFFFF" fill-opacity="0.2" />
  <rect x="72" y="330" width="1056" height="230" rx="28" fill="#0F172A" fill-opacity="0.28" stroke="#FFFFFF" stroke-opacity="0.12" />
  <text x="72" y="320" fill="#F8FAFC" fill-opacity="0.9" font-family="Arial, sans-serif" font-size="24">Scene guide</text>
  {detail_text}
  <rect x="72" y="606" width="1056" height="144" rx="28" fill="#0F172A" fill-opacity="0.24" stroke="#FFFFFF" stroke-opacity="0.12" />
  <text x="72" y="596" fill="#F8FAFC" fill-opacity="0.88" font-family="Arial, sans-serif" font-size="22">Prompt package excerpt</text>
  {prompt_text}
  <text x="72" y="790" fill="#F8FAFC" fill-opacity="0.88" font-family="Arial, sans-serif" font-size="26">Structured mock illustration generated for local review</text>
  <text x="72" y="828" fill="#CBD5E1" font-family="Arial, sans-serif" font-size="22">This placeholder now mirrors the page scene, characters, and location package.</text>
</svg>
"""
    return svg.encode("utf-8")


def _apply_regeneration_feedback_to_prompt(base_prompt: str, generation_notes: str | None) -> str:
    if not generation_notes or not generation_notes.strip():
        return base_prompt
    cleaned_notes = " ".join(generation_notes.split())
    return (
        f"{base_prompt.strip()}\n\n"
        "Revision feedback to fix in the next version:\n"
        f"- {cleaned_notes}\n"
        "- Correct the issues above while preserving approved story continuity, characters, and setting details.\n"
        "- Return a clearly improved image rather than a small variation of the rejected one."
    ).strip()


def get_story_page_or_404(session: Session, story_page_id: int) -> StoryPage:
    story_page = session.get(StoryPage, story_page_id)
    if story_page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story page not found")
    return story_page


def get_illustration_or_404(session: Session, illustration_id: int) -> Illustration:
    illustration = session.get(Illustration, illustration_id)
    if illustration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Illustration not found")
    return illustration


def validate_approval_status(approval_status: str) -> str:
    if approval_status not in ALLOWED_APPROVAL_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid approval status")
    return approval_status


def validate_provider(provider: str) -> str:
    normalized = provider.strip()
    if normalized == "live":
        normalized = "openai"
    if normalized not in ALLOWED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider")
    return normalized


def get_default_provider() -> str:
    configured = (ILLUSTRATION_GENERATION_PROVIDER or "mock").strip()
    if not configured:
        return "mock"
    try:
        return validate_provider(configured)
    except HTTPException:
        return "mock"


def resolve_provider(provider: str | None) -> str:
    if provider is None:
        return get_default_provider()
    return validate_provider(provider)


def persist_illustration(session: Session, illustration: Illustration) -> Illustration:
    session.add(illustration)
    session.commit()
    session.refresh(illustration)
    return illustration


def get_latest_illustration_for_page(session: Session, story_page_id: int) -> Illustration | None:
    statement = (
        select(Illustration)
        .where(Illustration.story_page_id == story_page_id)
        .order_by(desc(Illustration.version_number), desc(Illustration.created_at))
    )
    return session.exec(statement).first()


def determine_next_version_number(session: Session, story_page_id: int) -> int:
    latest = get_latest_illustration_for_page(session, story_page_id)
    return 1 if latest is None else latest.version_number + 1


def get_latest_approved_illustration_for_page(session: Session, story_page_id: int) -> Illustration | None:
    statement = (
        select(Illustration)
        .where(
            Illustration.story_page_id == story_page_id,
            Illustration.approval_status == "approved",
        )
        .order_by(desc(Illustration.version_number), desc(Illustration.created_at))
    )
    return session.exec(statement).first()


def set_story_page_status_from_latest_illustration(session: Session, story_page: StoryPage) -> StoryPage:
    latest = get_latest_illustration_for_page(session, story_page.id)
    latest_approved = get_latest_approved_illustration_for_page(session, story_page.id)
    if latest_approved is not None:
        story_page.image_status = "image_approved"
        story_page.image_url = latest_approved.image_url
    elif latest is None:
        story_page.image_status = "prompt_ready"
        story_page.image_url = None
    elif latest.approval_status == "rejected":
        story_page.image_status = "image_rejected"
        story_page.image_url = None
    else:
        story_page.image_status = "image_generated"
        story_page.image_url = latest.image_url

    story_page.updated_at = utc_now()
    session.add(story_page)
    session.commit()
    session.refresh(story_page)
    return story_page


def generate_mock_illustration(
    session: Session,
    *,
    story_page: StoryPage,
    override_prompt: str | None = None,
    generation_notes: str | None = None,
) -> Illustration:
    prompt_package = build_illustration_generation_package(
        session=session,
        story_page=story_page,
        provider="mock",
        override_prompt=override_prompt,
    )
    version_number = determine_next_version_number(session, story_page.id)
    asset_path = build_mock_image_path(
        story_draft_id=story_page.story_draft_id,
        page_number=story_page.page_number,
        version_number=version_number,
    )
    save_bytes(asset_path, _build_mock_illustration_svg(story_page=story_page, prompt_package=prompt_package))
    image_url = get_asset_url(asset_path)

    illustration = Illustration(
        story_page_id=story_page.id,
        prompt_used=prompt_package.prompt_used,
        image_url=image_url,
        version_number=version_number,
        approval_status="generated",
        provider="mock",
        generation_notes=generation_notes,
    )
    session.add(illustration)
    session.commit()
    session.refresh(illustration)

    story_page.image_status = "image_generated"
    story_page.image_url = illustration.image_url
    story_page.updated_at = utc_now()
    session.add(story_page)
    session.commit()
    session.refresh(story_page)
    return illustration


def _persist_generated_illustration(
    session: Session,
    *,
    story_page: StoryPage,
    provider: str,
    prompt_package: IllustrationGenerationPackage,
    image_url: str,
    version_number: int,
    provider_image_id: str | None = None,
    generation_notes: str | None = None,
) -> Illustration:
    illustration = Illustration(
        story_page_id=story_page.id,
        prompt_used=prompt_package.prompt_used,
        image_url=image_url,
        version_number=version_number,
        approval_status="generated",
        provider=provider,
        provider_image_id=provider_image_id,
        generation_notes=generation_notes,
    )
    session.add(illustration)
    session.commit()
    session.refresh(illustration)

    story_page.image_status = "image_generated"
    story_page.image_url = illustration.image_url
    story_page.updated_at = utc_now()
    session.add(story_page)
    session.commit()
    session.refresh(story_page)
    return illustration


def generate_illustration_asset(
    session: Session,
    *,
    story_page: StoryPage,
    provider: str | None,
    override_prompt: str | None = None,
    generation_notes: str | None = None,
) -> Illustration:
    provider = resolve_provider(provider)
    effective_override_prompt = _apply_regeneration_feedback_to_prompt(
        override_prompt or story_page.illustration_prompt,
        generation_notes,
    )
    if provider == "mock":
        return generate_mock_illustration(
            session,
            story_page=story_page,
            override_prompt=effective_override_prompt,
            generation_notes=generation_notes,
        )

    if provider in ALLOWED_LIVE_PROVIDERS:
        prompt_package = build_illustration_generation_package(
            session=session,
            story_page=story_page,
            provider=provider,
            override_prompt=effective_override_prompt,
        )
        if not prompt_package.live_generation_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "A live illustration provider is not configured yet. "
                    "Use the prompt preview endpoint to inspect the structured page package, "
                    "or continue generating mock illustrations for review."
                ),
            )
        try:
            live_result = generate_live_illustration_image(prompt_package)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Live illustration provider request failed with status {exc.response.status_code}.",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Live illustration generation failed: {exc}",
            ) from exc

        version_number = determine_next_version_number(session, story_page.id)
        asset_path = build_generated_image_path(
            story_draft_id=story_page.story_draft_id,
            page_number=story_page.page_number,
            version_number=version_number,
            extension=live_result.file_extension,
        )
        save_bytes(asset_path, live_result.image_bytes)
        image_url = get_asset_url(asset_path)
        notes = generation_notes
        if live_result.revised_prompt:
            revised_note = f"Provider revised prompt: {live_result.revised_prompt}"
            notes = f"{notes}\n{revised_note}".strip() if notes else revised_note
        return _persist_generated_illustration(
            session,
            story_page=story_page,
            provider=provider,
            prompt_package=prompt_package,
            image_url=image_url,
            version_number=version_number,
            provider_image_id=live_result.provider_image_id,
            generation_notes=notes,
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported illustration provider")


def approve_illustration(session: Session, illustration: Illustration) -> Illustration:
    validation_error = get_image_asset_validation_error(illustration.image_url)
    if validation_error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve illustration because its stored image is invalid. {validation_error}",
        )
    illustration.approval_status = "approved"
    illustration.updated_at = utc_now()
    session.add(illustration)
    session.commit()
    session.refresh(illustration)

    story_page = get_story_page_or_404(session, illustration.story_page_id)
    set_story_page_status_from_latest_illustration(session, story_page)
    session.refresh(illustration)
    return illustration


def reject_illustration(
    session: Session,
    illustration: Illustration,
    generation_notes: str | None = None,
) -> Illustration:
    illustration.approval_status = "rejected"
    if generation_notes is not None:
        illustration.generation_notes = generation_notes
    illustration.updated_at = utc_now()
    session.add(illustration)
    session.commit()
    session.refresh(illustration)

    story_page = get_story_page_or_404(session, illustration.story_page_id)
    set_story_page_status_from_latest_illustration(session, story_page)
    session.refresh(illustration)
    return illustration
