from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
import sqlite3
import sys
import traceback
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import ILLUSTRATION_GENERATION_API_KEY, ILLUSTRATION_GENERATION_BASE_URL, ILLUSTRATION_GENERATION_MODEL
from app.models.story_draft import StoryDraft
from app.models.story_idea import StoryIdea
from app.services.illustration_generation_service import _quality_reference_prompt, _rendering_requirements
from app.services.illustration_planner import generate_story_page_payloads
from app.services.storage_service import build_generated_image_path, get_local_asset_path

BOOK_ID = 1
STORY_DRAFT_ID = 3
ARTWORK_ROOT = ROOT / "Artwork" / "BuddyBug Character Bible"
PREVIEW_HTML = ROOT / "book-preview-story-1.html"


def _to_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _load_story_models(conn: sqlite3.Connection) -> tuple[StoryDraft, StoryIdea]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    draft = cur.execute("SELECT * FROM storydraft WHERE id = ?", (STORY_DRAFT_ID,)).fetchone()
    if draft is None:
        raise RuntimeError(f"Story draft {STORY_DRAFT_ID} not found")
    idea = cur.execute("SELECT * FROM storyidea WHERE id = ?", (draft["story_idea_id"],)).fetchone()
    if idea is None:
        raise RuntimeError(f"Story idea {draft['story_idea_id']} not found")

    story_draft = StoryDraft(
        id=draft["id"],
        story_idea_id=draft["story_idea_id"],
        title=draft["title"],
        age_band=draft["age_band"] if "age_band" in draft.keys() else "3-7",
        language="en",
        content_lane_key="bedtime_3_7",
        full_text=draft["full_text"],
        summary=draft["summary"],
        read_time_minutes=draft["read_time_minutes"],
        review_status=draft["review_status"],
        review_notes=draft["review_notes"],
        approved_text=draft["approved_text"],
        generation_source=draft["generation_source"],
    )
    story_idea = StoryIdea(
        id=idea["id"],
        title=idea["title"],
        premise=idea["premise"],
        hook_type=None,
        age_band=idea["age_band"],
        content_lane_key="bedtime_3_7",
        tone=idea["tone"],
        setting=idea["setting"],
        theme=idea["theme"],
        bedtime_feeling=idea["bedtime_feeling"],
        main_characters=idea["main_characters"],
        supporting_characters=idea["supporting_characters"],
        series_key=None,
        series_title=None,
        estimated_minutes=idea["estimated_minutes"],
        status=idea["status"],
        generation_source=idea["generation_source"],
    )
    return story_draft, story_idea


def _pages_to_generate(conn: sqlite3.Connection) -> list[int]:
    rows = conn.execute(
        "SELECT page_number FROM bookpage WHERE book_id = ? AND page_number >= 2 AND image_url IS NULL ORDER BY page_number ASC",
        (BOOK_ID,),
    ).fetchall()
    return [int(row[0]) for row in rows]


def _reference_paths_for_page(page_payload: dict[str, Any]) -> list[Path]:
    location = str(page_payload["location"]).casefold()
    chars = {name.strip() for name in str(page_payload["characters_present"]).split(",") if name.strip()}
    style_ref = (
        ARTWORK_ROOT / "Generated-quality-reference-v5-pixar-basket-bedtime.png"
        if any(token in location for token in ("bedroom", "window", "house"))
        else ARTWORK_ROOT / "Generated-quality-reference-v4-pixar-moonlit-garden.png"
    )
    refs = [
        style_ref,
        ARTWORK_ROOT / "Universe-core-cast-turnaround-sheet.png",
        ARTWORK_ROOT / "Dolly" / "Dolly-character-expression-board.png",
        ARTWORK_ROOT / "Daphne" / "Daphne-character-expression-board.png",
    ]
    if "Buddybug" in chars:
        refs[-1] = ARTWORK_ROOT / "BuddyBug" / "BuddyBug-character-expression-board.png"
    missing = [path for path in refs if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing reference files: {missing}")
    return refs


def _live_prompt(page_payload: dict[str, Any]) -> str:
    base_prompt = str(page_payload["illustration_prompt"]).strip()
    return "\n\n".join([base_prompt, _quality_reference_prompt(), _rendering_requirements()])


def _generate_page_image(page_payload: dict[str, Any]) -> bytes:
    if not ILLUSTRATION_GENERATION_API_KEY:
        raise RuntimeError("ILLUSTRATION_GENERATION_API_KEY is not configured")
    prompt = _live_prompt(page_payload)
    refs = _reference_paths_for_page(page_payload)
    payload = {
        "model": ILLUSTRATION_GENERATION_MODEL or "gpt-image-1.5",
        "prompt": prompt,
        "images": [{"image_url": _to_data_url(path)} for path in refs],
        "input_fidelity": "high",
        "size": "1024x1536",
        "quality": "high",
        "output_format": "png",
    }
    headers = {
        "Authorization": f"Bearer {ILLUSTRATION_GENERATION_API_KEY}",
        "Content-Type": "application/json",
    }
    response = httpx.post(
        ILLUSTRATION_GENERATION_BASE_URL.rstrip("/") + "/images/edits",
        headers=headers,
        json=payload,
        timeout=240,
    )
    response.raise_for_status()
    return base64.b64decode(response.json()["data"][0]["b64_json"])


def _attach_generated_page(
    conn: sqlite3.Connection,
    *,
    page_payload: dict[str, Any],
    page_number: int,
    image_bytes: bytes,
) -> str:
    story_page_id = conn.execute(
        "SELECT id FROM storypage WHERE story_draft_id = ? AND page_number = ?",
        (STORY_DRAFT_ID, page_number),
    ).fetchone()[0]
    existing = conn.execute(
        "SELECT COALESCE(MAX(version_number), 0) FROM illustration WHERE story_page_id = ?",
        (story_page_id,),
    ).fetchone()[0]
    version_number = int(existing or 0) + 1
    asset_path = build_generated_image_path(
        story_draft_id=STORY_DRAFT_ID,
        page_number=page_number,
        version_number=version_number,
        extension="png",
    )
    local_path = get_local_asset_path(asset_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(image_bytes)
    public_url = f"/{asset_path.replace('\\', '/')}"

    conn.execute(
        """
        UPDATE storypage
        SET illustration_prompt = ?, image_status = ?, image_url = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (str(page_payload["illustration_prompt"]), "image_generated", public_url, story_page_id),
    )
    conn.execute(
        """
        UPDATE bookpage
        SET image_url = ?, updated_at = CURRENT_TIMESTAMP
        WHERE book_id = ? AND page_number = ?
        """,
        (public_url, BOOK_ID, page_number),
    )
    conn.execute(
        """
        INSERT INTO illustration (
            story_page_id, prompt_used, image_url, version_number, approval_status,
            provider, provider_image_id, generation_notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            story_page_id,
            str(page_payload["illustration_prompt"]),
            public_url,
            version_number,
            "generated",
            "openai",
            None,
            "Generated from page-aware preview pipeline",
        ),
    )
    conn.commit()
    return public_url


def _rebuild_preview_html(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    pages = conn.execute(
        "SELECT page_number, text_content, image_url FROM bookpage WHERE book_id = ? ORDER BY page_number ASC",
        (BOOK_ID,),
    ).fetchall()

    sections: list[str] = []
    for row in pages:
        page_number = int(row["page_number"])
        heading = "Cover" if page_number == 0 else f"Page {page_number}"
        body = str(row["text_content"] or "")
        image_url = str(row["image_url"] or "")
        image_block = (
            f'<img src="http://127.0.0.1:8765{image_url.replace("/mock-assets/", "/storage/mock-assets/")}" alt="{heading} illustration">'
            if image_url
            else '<div class="placeholder">No illustration attached yet</div>'
        )
        title_block = "<h1>Verity and Dolly in the Moonlit Garden</h1>" if page_number == 0 else ""
        sections.append(
            f"""
    <section class="page">
      <div>
        <div class="page-number">{heading}</div>
        {title_block}
        <p class="text">{body}</p>
      </div>
      <div>
        {image_block}
      </div>
    </section>
"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BuddyBug Book Preview</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f4efe8; color: #2b241f; }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .note {{ margin-bottom: 20px; padding: 12px 16px; border-radius: 12px; background: #fff7d6; border: 1px solid #ecd98b; }}
    .page {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; align-items: center; background: #ffffff; border-radius: 18px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08); }}
    .page img {{ width: 100%; border-radius: 16px; background: #f2f2f2; border: 1px solid #ddd; }}
    .page-number {{ font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: #7a6553; margin-bottom: 10px; }}
    h1 {{ margin-top: 0; }}
    .placeholder {{ min-height: 260px; display: flex; align-items: center; justify-content: center; border: 2px dashed #cbbcae; border-radius: 16px; color: #7a6553; background: #faf7f2; text-align: center; padding: 20px; }}
    .text {{ line-height: 1.6; white-space: pre-wrap; }}
    @media (max-width: 850px) {{ .page {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="note">
      Live local preview of the current published BuddyBug book pages and attached illustrations.
    </div>
{''.join(sections)}
  </div>
</body>
</html>
"""
    PREVIEW_HTML.write_text(html, encoding="utf-8")


def main() -> None:
    conn = sqlite3.connect(ROOT / "buddybug.db")
    try:
        story_draft, story_idea = _load_story_models(conn)
        payloads = generate_story_page_payloads(
            story_draft=story_draft,
            story_idea=story_idea,
            target_page_count=None,
            min_pages=8,
            max_pages=10,
        )
        payload_by_page = {int(item["page_number"]): item for item in payloads}
        requested_pages = sorted({int(arg) for arg in sys.argv[1:]}) if len(sys.argv) > 1 else []
        targets = requested_pages or _pages_to_generate(conn)
        if not targets:
            print("No missing book pages to generate.")
            _rebuild_preview_html(conn)
            return
        print(f"Target pages: {targets}", flush=True)
        for page_number in targets:
            page_payload = payload_by_page[page_number]
            print(f"Generating page {page_number}...", flush=True)
            image_bytes = _generate_page_image(page_payload)
            public_url = _attach_generated_page(
                conn,
                page_payload=page_payload,
                page_number=page_number,
                image_bytes=image_bytes,
            )
            print(f"Attached page {page_number}: {public_url}", flush=True)
        _rebuild_preview_html(conn)
        print(f"Updated preview: {PREVIEW_HTML}", flush=True)
    except Exception:
        traceback.print_exc()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
