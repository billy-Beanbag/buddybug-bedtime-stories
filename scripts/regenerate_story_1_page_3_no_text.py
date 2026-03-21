from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
import sqlite3
import sys

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import ILLUSTRATION_GENERATION_API_KEY, ILLUSTRATION_GENERATION_BASE_URL, ILLUSTRATION_GENERATION_MODEL
from app.services.illustration_generation_service import _quality_reference_prompt, _rendering_requirements
from app.services.storage_service import build_generated_image_path, get_local_asset_path

BOOK_ID = 1
STORY_DRAFT_ID = 3
PAGE_NUMBER = 3
ARTWORK_ROOT = ROOT / "Artwork" / "BuddyBug Character Bible"
PREVIEW_HTML = ROOT / "book-preview-story-1.html"


def _to_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _generate(prompt: str) -> bytes:
    refs = [
        ARTWORK_ROOT / "Generated-quality-reference-v4-pixar-moonlit-garden.png",
        ARTWORK_ROOT / "Universe-core-cast-turnaround-sheet.png",
        ARTWORK_ROOT / "Dolly" / "Dolly-character-expression-board.png",
        ARTWORK_ROOT / "Daphne" / "Daphne-character-expression-board.png",
    ]
    missing = [path for path in refs if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing reference files: {missing}")
    payload = {
        "model": ILLUSTRATION_GENERATION_MODEL or "gpt-image-1.5",
        "prompt": "\n\n".join([prompt.strip(), _quality_reference_prompt(), _rendering_requirements()]),
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
        rendered_url = image_url
        if rendered_url.startswith("/mock-assets/"):
            rendered_url = rendered_url.replace("/mock-assets/", "/storage/mock-assets/")
        image_block = (
            f'<img src="http://127.0.0.1:8765{rendered_url}" alt="{heading} illustration">'
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
      Updated local preview after page 3 no-text illustration fix.
    </div>
{''.join(sections)}
  </div>
</body>
</html>
"""
    PREVIEW_HTML.write_text(html, encoding="utf-8")


def main() -> None:
    prompt = """
Create one children's storybook illustration for a single story page.

Page number: 3
Scene location: moonlit garden
Characters present: Verity, Dolly, Daphne.
Key action: Verity shares a warm reassuring look with Dolly and Daphne beside moonlit flowers while the three pause together in a gentle glowing moment.
Emotional tone: calm reassurance, closeness, gentle wonder.
Important objects: flowers, glowing path, moonlight.
Time of day and lighting: soft moonlight with warm magical highlights, crisp faces, clear collars, and a gentle bedtime glow.
Composition note: close comforting outdoor composition with one clear caring gesture and both dogs clearly visible beside Verity.

Critical no-text requirement:
Do not place any text anywhere in the image. No captions, no writing, no story words, no page text, no labels, no letters, no watermark, no signature, and no readable markings on any object.

Story relevance:
This is still outdoors in the moonlit garden. It is a gentle pause in the story, not a book page showing printed words.

Negative prompt:
no text; no captions; no writing in the image; no visible letters; no subtitle-like text at the bottom; no watermark; no bed; no sleeping.
""".strip()

    conn = sqlite3.connect(ROOT / "buddybug.db")
    try:
        image_bytes = _generate(prompt)
        story_page_id = conn.execute(
            "SELECT id FROM storypage WHERE story_draft_id = ? AND page_number = ?",
            (STORY_DRAFT_ID, PAGE_NUMBER),
        ).fetchone()[0]
        existing = conn.execute(
            "SELECT COALESCE(MAX(version_number), 0) FROM illustration WHERE story_page_id = ?",
            (story_page_id,),
        ).fetchone()[0]
        version_number = int(existing or 0) + 1
        asset_path = build_generated_image_path(
            story_draft_id=STORY_DRAFT_ID,
            page_number=PAGE_NUMBER,
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
            (prompt, "image_generated", public_url, story_page_id),
        )
        conn.execute(
            """
            UPDATE bookpage
            SET image_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE book_id = ? AND page_number = ?
            """,
            (public_url, BOOK_ID, PAGE_NUMBER),
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
                prompt,
                public_url,
                version_number,
                "generated",
                "openai",
                None,
                "Regenerated to remove accidental text inside artwork",
            ),
        )
        conn.commit()
        _rebuild_preview_html(conn)
        print(public_url)
        print(f"Updated preview: {PREVIEW_HTML}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
