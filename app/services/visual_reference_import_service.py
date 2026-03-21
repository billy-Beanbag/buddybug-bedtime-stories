from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, select

from app.config import PROJECT_ROOT
from app.database import create_db_and_tables, required_tables_exist
from app.models import Character, ContentLane, EditorialProject, VisualReferenceAsset
from app.services.visual_reference_service import create_visual_reference_asset, update_visual_reference_asset

CHARACTER_BIBLE_ROOT = PROJECT_ROOT / "Artwork" / "BuddyBug Character Bible"
ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
CHARACTER_FOLDER_TO_NAME = {
    "Verity": "Verity",
    "Daphne": "Daphne",
    "Dolly": "Dolly",
    "BuddyBug": "Buddybug",
    "GlowMoth": "Glowmoth",
    "Twinklet": "Twinklet",
    "Whisperwing": "Whisperwing",
}


@dataclass(frozen=True)
class VisualReferenceImportResult:
    created: int
    updated: int
    scanned: int


def artwork_relative_path(raw_path: str) -> str:
    cleaned = raw_path.strip().replace("\\", "/").lstrip("/")
    if cleaned.casefold().startswith("artwork/"):
        cleaned = cleaned.split("/", 1)[1]
    if not cleaned:
        raise ValueError("Artwork path cannot be empty")
    file_path = PROJECT_ROOT / "Artwork" / cleaned
    if not file_path.exists():
        raise FileNotFoundError(f"Artwork file not found: {file_path}")
    return cleaned


def _resolve_target(session: Session, entry: dict) -> tuple[str | None, int | None]:
    target_type = entry.get("target_type")
    if not target_type:
        return None, None

    target_id = entry.get("target_id")
    if isinstance(target_id, int):
        return target_type, target_id

    if target_type == "character":
        target_name = str(entry.get("target_name") or "").strip()
        character = session.exec(select(Character).where(Character.name == target_name)).first()
        if character is None:
            raise ValueError(f"Character target not found: {target_name}")
        return target_type, character.id

    if target_type == "content_lane":
        lane_key = str(entry.get("target_key") or entry.get("target_name") or "").strip()
        lane = session.exec(select(ContentLane).where(ContentLane.key == lane_key)).first()
        if lane is None:
            raise ValueError(f"Content lane target not found: {lane_key}")
        return target_type, lane.id

    if target_type == "editorial_project":
        slug = str(entry.get("target_slug") or entry.get("target_name") or "").strip()
        project = session.exec(select(EditorialProject).where(EditorialProject.slug == slug)).first()
        if project is None:
            raise ValueError(f"Editorial project target not found: {slug}")
        return target_type, project.id

    raise ValueError(f"target_id is required for target_type={target_type}")


def _find_existing_asset(
    session: Session,
    *,
    name: str,
    reference_type: str,
    target_type: str | None,
    target_id: int | None,
) -> VisualReferenceAsset | None:
    statement = select(VisualReferenceAsset).where(
        VisualReferenceAsset.name == name,
        VisualReferenceAsset.reference_type == reference_type,
    )
    if target_type is None:
        statement = statement.where(
            VisualReferenceAsset.target_type.is_(None),
            VisualReferenceAsset.target_id.is_(None),
        )
    else:
        statement = statement.where(
            VisualReferenceAsset.target_type == target_type,
            VisualReferenceAsset.target_id == target_id,
        )
    return session.exec(statement).first()


def _read_optional_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _read_first_matching_text(directory: Path, pattern: str) -> str:
    for candidate in sorted(directory.glob(pattern)):
        if candidate.is_file():
            return _read_optional_text(candidate)
    return ""


def _to_artwork_relative_path(file_path: Path) -> str:
    try:
        relative = file_path.relative_to(PROJECT_ROOT / "Artwork")
    except ValueError as exc:
        raise ValueError(f"Path is not inside Artwork: {file_path}") from exc
    return relative.as_posix()


def _humanize_stem(stem: str) -> str:
    return stem.replace("-", " ").replace("_", " ").strip()


def _character_prompt_notes(*, global_notes: str, character_notes: str) -> str | None:
    sections: list[str] = []
    if global_notes:
        sections.append(f"Global Storylight rules:\n{global_notes}")
    if character_notes:
        sections.append(f"Character-specific reference:\n{character_notes}")
    return "\n\n".join(section for section in sections if section).strip() or None


def build_character_bible_manifest() -> list[dict[str, object]]:
    if not CHARACTER_BIBLE_ROOT.exists():
        raise FileNotFoundError(f"Character bible folder not found: {CHARACTER_BIBLE_ROOT}")

    global_notes = _read_optional_text(CHARACTER_BIBLE_ROOT / "The Buddybug Storylight Character Bible.txt")
    manifest: list[dict[str, object]] = []

    for file_path in sorted(CHARACTER_BIBLE_ROOT.rglob("*")):
        if not file_path.is_file() or file_path.suffix.casefold() not in ALLOWED_IMAGE_SUFFIXES:
            continue

        relative_to_bible = file_path.relative_to(CHARACTER_BIBLE_ROOT)
        path_parts = relative_to_bible.parts
        if len(path_parts) >= 2 and path_parts[0] in CHARACTER_FOLDER_TO_NAME:
            folder_name = path_parts[0]
            if not file_path.stem.casefold().startswith(folder_name.casefold()):
                continue
            character_name = CHARACTER_FOLDER_TO_NAME[folder_name]
            character_notes = _read_first_matching_text(
                CHARACTER_BIBLE_ROOT / folder_name,
                "*Character Reference.txt",
            )
            manifest.append(
                {
                    "name": _humanize_stem(file_path.stem),
                    "reference_type": "character_sheet",
                    "target_type": "character",
                    "target_name": character_name,
                    "artwork_path": _to_artwork_relative_path(file_path),
                    "prompt_notes": _character_prompt_notes(
                        global_notes=global_notes,
                        character_notes=character_notes,
                    ),
                    "is_active": True,
                }
            )
            continue

        if not file_path.stem.casefold().startswith("universe-"):
            continue
        stem = file_path.stem.casefold()
        reference_type = "scene_reference" if ("world-map" in stem or "scene" in stem) else "style_reference"
        prompt_notes = global_notes or None
        if "world-map" in stem:
            extra = "Use this as a location and world-layout reference for the Storylight world."
            prompt_notes = f"{prompt_notes}\n\n{extra}".strip() if prompt_notes else extra
        elif "turnaround" in stem:
            extra = "Use this as a cast scale, turnaround, and proportion consistency reference."
            prompt_notes = f"{prompt_notes}\n\n{extra}".strip() if prompt_notes else extra
        elif "portrait" in stem or "basket" in stem:
            extra = "Use this as a cast composition, lighting, and mood reference."
            prompt_notes = f"{prompt_notes}\n\n{extra}".strip() if prompt_notes else extra

        manifest.append(
            {
                "name": _humanize_stem(file_path.stem),
                "reference_type": reference_type,
                "artwork_path": _to_artwork_relative_path(file_path),
                "prompt_notes": prompt_notes,
                "is_active": True,
            }
        )

    return manifest


def load_manifest_file(manifest_path: Path) -> list[dict[str, object]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a JSON array")
    return manifest


def import_entries(session: Session, manifest: list[dict[str, object]], *, dry_run: bool) -> VisualReferenceImportResult:
    created = 0
    updated = 0
    for entry in manifest:
        name = str(entry["name"]).strip()
        reference_type = str(entry["reference_type"]).strip()
        normalized_artwork_path = artwork_relative_path(str(entry["artwork_path"]))
        target_type, target_id = _resolve_target(session, entry)
        image_url = f"/artwork-assets/{normalized_artwork_path}"
        prompt_notes = entry.get("prompt_notes")
        language = entry.get("language")
        is_active = bool(entry.get("is_active", True))

        existing = _find_existing_asset(
            session,
            name=name,
            reference_type=reference_type,
            target_type=target_type,
            target_id=target_id,
        )
        if dry_run:
            continue

        if existing is None:
            create_visual_reference_asset(
                session,
                name=name,
                reference_type=reference_type,
                target_type=target_type,
                target_id=target_id,
                image_url=image_url,
                prompt_notes=str(prompt_notes).strip() if prompt_notes else None,
                language=str(language).strip() if language else None,
                is_active=is_active,
                created_by_user_id=None,
            )
            created += 1
        else:
            update_visual_reference_asset(
                session,
                asset=existing,
                image_url=image_url,
                prompt_notes=str(prompt_notes).strip() if prompt_notes else None,
                language=str(language).strip() if language else None,
                is_active=is_active,
                prompt_notes_provided=True,
                language_provided=True,
            )
            updated += 1
    return VisualReferenceImportResult(created=created, updated=updated, scanned=len(manifest))


def ensure_visual_reference_tables() -> bool:
    if required_tables_exist("visualreferenceasset"):
        return False
    create_db_and_tables()
    return True

