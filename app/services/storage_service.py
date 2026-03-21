from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlparse

from app.config import (
    S3_BUCKET_NAME,
    S3_ENDPOINT_URL,
    S3_REGION,
    STORAGE_BACKEND,
    STORAGE_LOCAL_BASE_PATH,
    STORAGE_PUBLIC_BASE_URL,
)


def _normalize_asset_path(path: str) -> str:
    cleaned = path.strip().lstrip("/").replace("\\", "/")
    if not cleaned:
        raise ValueError("Asset path cannot be empty")
    return cleaned


def get_asset_url(path: str) -> str:
    """Build a public URL for a stored asset path."""
    normalized_path = _normalize_asset_path(path)
    if STORAGE_BACKEND == "s3":
        if STORAGE_PUBLIC_BASE_URL:
            return urljoin(STORAGE_PUBLIC_BASE_URL.rstrip("/") + "/", quote(normalized_path))
        if S3_ENDPOINT_URL and S3_BUCKET_NAME:
            return urljoin(
                S3_ENDPOINT_URL.rstrip("/") + f"/{S3_BUCKET_NAME}/",
                quote(normalized_path),
            )
        if S3_BUCKET_NAME and S3_REGION:
            return f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{quote(normalized_path)}"
    return urljoin(STORAGE_PUBLIC_BASE_URL.rstrip("/") + "/", quote(normalized_path))


def get_local_asset_path(path: str) -> Path:
    return Path(STORAGE_LOCAL_BASE_PATH) / _normalize_asset_path(path)


def get_local_asset_path_from_url(path_or_url: str) -> Path:
    parsed = urlparse(path_or_url)
    normalized_path = unquote(parsed.path if parsed.scheme or parsed.netloc else path_or_url).lstrip("/")
    return get_local_asset_path(normalized_path)


def get_image_asset_validation_error(path_or_url: str | None) -> str | None:
    if not path_or_url:
        return "Image URL is missing."

    asset_path = get_local_asset_path_from_url(path_or_url)
    if not asset_path.exists() or not asset_path.is_file():
        return f"Stored image asset does not exist: {asset_path.name}."

    size = asset_path.stat().st_size
    if size <= 0:
        return f"Stored image asset is empty: {asset_path.name}."

    extension = asset_path.suffix.lower()
    header = asset_path.read_bytes()[:512]

    if extension == ".png":
        if size < 64 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
            return f"Stored PNG asset is invalid or truncated: {asset_path.name} ({size} bytes)."
    elif extension in {".jpg", ".jpeg"}:
        if size < 64 or not header.startswith(b"\xff\xd8\xff"):
            return f"Stored JPEG asset is invalid or truncated: {asset_path.name} ({size} bytes)."
    elif extension == ".webp":
        if size < 64 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
            return f"Stored WEBP asset is invalid or truncated: {asset_path.name} ({size} bytes)."
    elif extension == ".gif":
        if size < 64 or (not header.startswith(b"GIF87a") and not header.startswith(b"GIF89a")):
            return f"Stored GIF asset is invalid or truncated: {asset_path.name} ({size} bytes)."
    elif extension == ".svg":
        text_sample = header.decode("utf-8", errors="ignore").lower()
        if "<svg" not in text_sample:
            return f"Stored SVG asset is invalid or truncated: {asset_path.name} ({size} bytes)."

    return None


def build_mock_image_path(*, story_draft_id: int, page_number: int, version_number: int) -> str:
    return f"mock-assets/images/story-{story_draft_id}/page-{page_number}-v{version_number}.svg"


def build_mock_cover_path(*, story_draft_id: int, version_number: int) -> str:
    return f"mock-assets/images/story-{story_draft_id}/cover-v{version_number}.svg"


def build_generated_image_path(
    *,
    story_draft_id: int,
    page_number: int,
    version_number: int,
    extension: str = "png",
) -> str:
    cleaned_extension = extension.strip().lstrip(".") or "png"
    return f"mock-assets/images/generated/story-{story_draft_id}/page-{page_number}-v{version_number}.{cleaned_extension}"


def build_generated_cover_path(
    *,
    story_draft_id: int,
    version_number: int,
    extension: str = "png",
) -> str:
    cleaned_extension = extension.strip().lstrip(".") or "png"
    return f"mock-assets/images/generated/story-{story_draft_id}/cover-v{version_number}.{cleaned_extension}"


def build_mock_audio_path(*, book_id: int, voice_key: str, version_number: int) -> str:
    return f"mock-assets/audio/book-{book_id}/{voice_key}-v{version_number}.mp3"


def build_mock_narration_segment_path(
    *,
    book_id: int,
    voice_key: str,
    language: str,
    narration_id: int,
    page_number: int,
) -> str:
    return (
        f"mock-assets/narration/book-{book_id}/{language}/{voice_key}/"
        f"narration-{narration_id}-page-{page_number}.wav"
    )


def build_mock_download_package_path(*, book_id: int, language: str, version_number: int) -> str:
    return f"mock-assets/downloads/book-{book_id}/{language}-v{version_number}.json"


def save_bytes(path: str, content: bytes) -> str:
    """Save asset bytes for local storage. S3 upload is intentionally deferred."""
    normalized_path = _normalize_asset_path(path)
    if STORAGE_BACKEND == "s3":
        raise NotImplementedError("S3 uploads are not implemented yet")

    target_path = get_local_asset_path(normalized_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(content)
    return normalized_path
