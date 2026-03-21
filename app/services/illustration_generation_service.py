from __future__ import annotations

import base64
from collections.abc import Sequence
from dataclasses import dataclass
import logging
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from sqlmodel import Session

from app.config import (
    ILLUSTRATION_GENERATION_API_KEY,
    ILLUSTRATION_GENERATION_BASE_URL,
    ILLUSTRATION_GENERATION_DEBUG,
    ILLUSTRATION_GENERATION_MODEL,
    ILLUSTRATION_GENERATION_TIMEOUT_SECONDS,
    PROJECT_ROOT,
    STORAGE_LOCAL_BASE_PATH,
)
from app.models import StoryPage
from app.services.visual_reference_service import list_recommended_visual_references_for_story_page

logger = logging.getLogger(__name__)

MOCK_PROVIDER_MODEL = "mock-storyboard-svg-v1"
MAX_REFERENCE_IMAGES = 4


@dataclass(frozen=True)
class IllustrationReferenceAsset:
    id: int
    name: str
    reference_type: str
    target_type: str | None
    target_id: int | None
    image_url: str
    prompt_notes: str | None
    language: str | None
    is_active: bool


@dataclass(frozen=True)
class IllustrationGenerationPackage:
    story_page_id: int
    provider: str
    provider_model: str | None
    prompt_used: str
    positive_prompt: str
    negative_prompt: str
    page_text: str
    scene_summary: str
    location: str
    mood: str
    characters_present: str
    reference_assets: tuple[IllustrationReferenceAsset, ...]
    reference_summary: str
    generation_ready: bool
    live_generation_available: bool
    provider_base_url: str | None = None
    provider_timeout_seconds: int | None = None
    debug_enabled: bool = False


@dataclass(frozen=True)
class LiveIllustrationResult:
    image_bytes: bytes
    provider_image_id: str | None = None
    revised_prompt: str | None = None
    file_extension: str = "png"


def _split_prompt_sections(prompt_used: str) -> tuple[str, str]:
    lines = [line.strip() for line in prompt_used.splitlines() if line.strip()]
    positive_lines: list[str] = []
    negative_lines: list[str] = []
    for line in lines:
        if line.casefold().startswith("negative prompt:"):
            negative_lines.append(line.split(":", 1)[1].strip())
            continue
        positive_lines.append(line)
    return "\n".join(positive_lines).strip(), " ".join(negative_lines).strip()


def has_live_illustration_provider_config() -> bool:
    return bool(ILLUSTRATION_GENERATION_API_KEY and ILLUSTRATION_GENERATION_MODEL)


def _quality_reference_prompt() -> str:
    return "\n".join(
        [
            "Create a high-end Pixar-style animated illustration.",
            "",
            "Style:",
            "Pixar-style 3D animation rendering, ultra-detailed character expressions, soft cinematic lighting, warm color palette, high-quality animated film aesthetic.",
            "",
            "Lighting:",
            "soft bedtime lighting with warm golden glow, gentle moonlight, subtle magical firefly light, warm lamp glow, cozy nighttime atmosphere.",
            "",
            "Colour palette:",
            "warm golds, soft creams, pale blues, dusty lavender, gentle greens, warm amber highlights, pastel night tones.",
            "",
            "Composition:",
            "storybook composition, medium-close framing, characters centered and slightly forward, cozy environment surrounding them, shallow depth feeling, magical atmosphere, gentle background details.",
            "",
            "Mood:",
            "cozy bedtime, calm, magical, comforting, safe, dreamy.",
            "",
            "Environment:",
            "soft storybook setting with flowers, blankets, warm bedroom lighting or moonlit garden details, visible moon or window glow, subtle glowing particles and fireflies.",
            "",
            "Rendering:",
            "professional animated storybook quality, luminous highlights, cinematic warmth, polished surfaces, crisp facial features, crisp collars and markings, readable silhouettes, and controlled detail.",
            "",
            "Aspect:",
            "vertical illustration suitable for a storybook page.",
        ]
    )


def _rendering_requirements() -> str:
    return "\n".join(
        [
            "Rendering requirements:",
            "- Keep edges, eyes, collars, coat markings, and silhouettes clear and well defined.",
            "- Keep faces polished, eyes bright, and main subjects crisp enough for premium storybook printing.",
            "- Favor a premium animated-film finish over a heavy watercolor wash.",
            "- Allow softness in lighting and atmosphere, but avoid blurry contours or overly diffuse details.",
            "- Keep the image polished, bright, and production-ready rather than rough or sketchy.",
            "- Do not render any printed words, handwriting, captions, subtitles, lettering, logos, or watermarks inside the artwork.",
            "- If a book, sign, label, or page appears in the scene, keep it free of readable text.",
        ]
    )


def _build_live_prompt(package: IllustrationGenerationPackage) -> str:
    prompt_lines: list[str] = []
    for line in package.positive_prompt.splitlines():
        stripped = line.strip()
        if stripped.casefold().startswith("exact text:"):
            continue
        prompt_lines.append(line)
    sanitized_positive_prompt = "\n".join(prompt_lines).strip()

    sections = [
        sanitized_positive_prompt,
        "Use any narrative text only as scene context. Do not render any words or lettering inside the image.",
        _quality_reference_prompt(),
        _rendering_requirements(),
    ]
    if package.reference_summary:
        sections.extend(
            [
                "Highest-priority visual reference assets to follow:",
                package.reference_summary,
            ]
        )
    if package.negative_prompt:
        sections.extend(
            [
                "Important visual constraints:",
                package.negative_prompt,
            ]
        )
    return "\n\n".join(section for section in sections if section).strip()


def _images_generation_url() -> str:
    return ILLUSTRATION_GENERATION_BASE_URL.rstrip("/") + "/images/generations"


def _images_edits_url() -> str:
    return ILLUSTRATION_GENERATION_BASE_URL.rstrip("/") + "/images/edits"


def _guess_extension_from_url(url: str) -> str:
    lowered = url.casefold()
    for extension in ("png", "jpg", "jpeg", "webp"):
        if f".{extension}" in lowered:
            return extension
    return "png"


def _supports_reference_image_edits() -> bool:
    model = (ILLUSTRATION_GENERATION_MODEL or "").strip().casefold()
    return model.startswith("gpt-image-") or model == "chatgpt-image-latest"


def _guess_mime_type(name: str, *, fallback: str = "image/png") -> str:
    guessed, _ = mimetypes.guess_type(name)
    return guessed or fallback


def _to_data_url(image_bytes: bytes, *, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _resolve_local_reference_path(image_url: str) -> Path | None:
    parsed = urlparse(image_url)
    raw_path = parsed.path if parsed.scheme else image_url
    normalized = unquote(raw_path or "").strip()
    if not normalized:
        return None
    if normalized.startswith("/artwork-assets/"):
        return PROJECT_ROOT / "Artwork" / normalized.removeprefix("/artwork-assets/")
    if normalized.startswith("/mock-assets/"):
        return Path(STORAGE_LOCAL_BASE_PATH) / normalized.lstrip("/")
    if normalized.startswith("mock-assets/"):
        return Path(STORAGE_LOCAL_BASE_PATH) / normalized
    return None


def _load_reference_image_data_url(*, image_url: str, client: httpx.Client) -> str:
    if image_url.startswith("data:"):
        return image_url
    local_path = _resolve_local_reference_path(image_url)
    if local_path is not None and local_path.exists():
        return _to_data_url(local_path.read_bytes(), mime_type=_guess_mime_type(local_path.name))
    response = client.get(image_url)
    response.raise_for_status()
    content_type = response.headers.get("content-type") or _guess_mime_type(image_url)
    return _to_data_url(response.content, mime_type=content_type)


def _build_reference_inputs(
    package: IllustrationGenerationPackage,
    *,
    client: httpx.Client,
) -> list[dict[str, str]]:
    ranked_assets = sorted(
        package.reference_assets,
        key=lambda asset: (
            0 if asset.target_type == "character" else 1,
            0 if asset.reference_type == "character_sheet" else 1,
            0 if "turnaround" in asset.name.casefold() else 1,
            0 if "expression" in asset.name.casefold() else 1,
            0 if "style" in asset.name.casefold() else 1,
            asset.id,
        ),
    )
    inputs: list[dict[str, str]] = []
    for asset in ranked_assets[:MAX_REFERENCE_IMAGES]:
        try:
            inputs.append({"image_url": _load_reference_image_data_url(image_url=asset.image_url, client=client)})
        except Exception as exc:
            logger.warning(
                "Skipping illustration reference asset: story_page_id=%s asset_id=%s image_url=%s error=%s",
                package.story_page_id,
                asset.id,
                asset.image_url,
                exc,
            )
    return inputs


def _extract_image_data(payload: dict, *, client: httpx.Client) -> LiveIllustrationResult:
    data_items = payload.get("data") or []
    if not data_items:
        raise RuntimeError("Live illustration provider returned no image data")
    item = data_items[0] or {}
    if item.get("b64_json"):
        return LiveIllustrationResult(
            image_bytes=base64.b64decode(item["b64_json"]),
            provider_image_id=item.get("id"),
            revised_prompt=item.get("revised_prompt"),
            file_extension="png",
        )
    if item.get("b64"):
        return LiveIllustrationResult(
            image_bytes=base64.b64decode(item["b64"]),
            provider_image_id=item.get("id"),
            revised_prompt=item.get("revised_prompt"),
            file_extension="png",
        )
    if item.get("url"):
        image_response = client.get(str(item["url"]))
        image_response.raise_for_status()
        return LiveIllustrationResult(
            image_bytes=image_response.content,
            provider_image_id=item.get("id"),
            revised_prompt=item.get("revised_prompt"),
            file_extension=_guess_extension_from_url(str(item["url"])),
        )
    raise RuntimeError("Live illustration provider returned an unsupported image payload")


def _generate_live_image(
    *,
    prompt: str,
    reference_image_urls: Sequence[str],
    size: str,
    debug_context: str,
    client: httpx.Client | None = None,
) -> LiveIllustrationResult:
    if not has_live_illustration_provider_config():
        raise RuntimeError("Live illustration provider is not configured")

    headers = {
        "Authorization": f"Bearer {ILLUSTRATION_GENERATION_API_KEY}",
        "Content-Type": "application/json",
    }

    created_client = client is None
    if created_client:
        client = httpx.Client(timeout=ILLUSTRATION_GENERATION_TIMEOUT_SECONDS)

    assert client is not None
    try:
        reference_inputs: list[dict[str, str]] = []
        for image_url in list(reference_image_urls)[:MAX_REFERENCE_IMAGES]:
            try:
                reference_inputs.append(
                    {
                        "image_url": _load_reference_image_data_url(
                            image_url=image_url,
                            client=client,
                        )
                    }
                )
            except Exception as exc:
                logger.warning(
                    "Skipping cover/reference image: context=%s image_url=%s error=%s",
                    debug_context,
                    image_url,
                    exc,
                )

        use_reference_edits = bool(reference_inputs) and _supports_reference_image_edits()
        payload = {
            "model": ILLUSTRATION_GENERATION_MODEL,
            "prompt": prompt,
            "size": size,
            "quality": "high",
            "output_format": "png",
        }
        url = _images_generation_url()
        if use_reference_edits:
            payload["images"] = reference_inputs
            payload["input_fidelity"] = "high"
            url = _images_edits_url()

        response = client.post(
            url,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        parsed = response.json()
        if ILLUSTRATION_GENERATION_DEBUG:
            logger.info(
                "Live image generation succeeded: model=%s context=%s reference_images=%s endpoint=%s",
                ILLUSTRATION_GENERATION_MODEL,
                debug_context,
                len(reference_inputs),
                url,
            )
        return _extract_image_data(parsed, client=client)
    except httpx.HTTPStatusError:
        if ILLUSTRATION_GENERATION_DEBUG:
            logger.error(
                "Live image generation failed: context=%s status_code=%s response_body=%s",
                debug_context,
                response.status_code,
                response.text,
            )
        raise
    finally:
        if created_client:
            client.close()


def generate_live_illustration_image(
    package: IllustrationGenerationPackage,
    *,
    client: httpx.Client | None = None,
) -> LiveIllustrationResult:
    # Reuse the generic live image path so cover generation can share the same provider logic.
    reference_inputs = tuple(asset.image_url for asset in package.reference_assets)
    return _generate_live_image(
        prompt=_build_live_prompt(package),
        reference_image_urls=reference_inputs,
        size="1024x1536",
        debug_context=f"story_page:{package.story_page_id}",
        client=client,
    )


def generate_live_image_from_prompt(
    *,
    prompt: str,
    reference_image_urls: Sequence[str] | None = None,
    size: str = "1536x1024",
    debug_context: str = "generic",
    client: httpx.Client | None = None,
) -> LiveIllustrationResult:
    return _generate_live_image(
        prompt=prompt,
        reference_image_urls=tuple(reference_image_urls or ()),
        size=size,
        debug_context=debug_context,
        client=client,
    )


def build_illustration_generation_package(
    *,
    session: Session | None,
    story_page: StoryPage,
    provider: str,
    override_prompt: str | None = None,
) -> IllustrationGenerationPackage:
    prompt_used = (override_prompt or story_page.illustration_prompt).strip()
    positive_prompt, negative_prompt = _split_prompt_sections(prompt_used)
    reference_assets: tuple[IllustrationReferenceAsset, ...] = ()
    reference_summary = ""
    if session is not None:
        recommended_assets = list_recommended_visual_references_for_story_page(
            session,
            story_page_id=story_page.id,
            include_inactive=False,
        )
        ranked_assets = sorted(
            recommended_assets,
            key=lambda asset: (
                0 if asset.target_type == "character" else 1,
                0 if asset.reference_type == "character_sheet" else 1,
                0 if "turnaround" in asset.name.casefold() else 1,
                0 if "expression" in asset.name.casefold() else 1,
                0 if "style" in asset.name.casefold() else 1,
                asset.id,
            ),
        )
        reference_assets = tuple(
            IllustrationReferenceAsset(
                id=asset.id,
                name=asset.name,
                reference_type=asset.reference_type,
                target_type=asset.target_type,
                target_id=asset.target_id,
                image_url=asset.image_url,
                prompt_notes=asset.prompt_notes,
                language=asset.language,
                is_active=asset.is_active,
            )
            for asset in ranked_assets
        )
        reference_lines: list[str] = []
        for asset in reference_assets[:MAX_REFERENCE_IMAGES]:
            line = f"- {asset.reference_type}: {asset.name} ({asset.image_url})"
            if asset.prompt_notes:
                line += f" | Notes: {asset.prompt_notes}"
            reference_lines.append(line)
        reference_summary = "\n".join(reference_lines)
    live_generation_available = has_live_illustration_provider_config()
    provider_model = MOCK_PROVIDER_MODEL if provider == "mock" else (ILLUSTRATION_GENERATION_MODEL or None)
    provider_base_url = None if provider == "mock" else (ILLUSTRATION_GENERATION_BASE_URL or None)
    provider_timeout_seconds = None if provider == "mock" else ILLUSTRATION_GENERATION_TIMEOUT_SECONDS
    return IllustrationGenerationPackage(
        story_page_id=story_page.id,
        provider=provider,
        provider_model=provider_model,
        prompt_used=prompt_used,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        page_text=story_page.page_text,
        scene_summary=story_page.scene_summary,
        location=story_page.location,
        mood=story_page.mood,
        characters_present=story_page.characters_present,
        reference_assets=reference_assets,
        reference_summary=reference_summary,
        generation_ready=bool(positive_prompt and story_page.page_text and story_page.scene_summary),
        live_generation_available=live_generation_available,
        provider_base_url=provider_base_url,
        provider_timeout_seconds=provider_timeout_seconds,
        debug_enabled=ILLUSTRATION_GENERATION_DEBUG if provider != "mock" else False,
    )
