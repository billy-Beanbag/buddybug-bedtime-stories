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
ARTWORK_ROOT = ROOT / "Artwork" / "BuddyBug Character Bible"
PREVIEW_HTML = ROOT / "book-preview-story-1.html"


def _to_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _reference_paths(style: str) -> list[Path]:
    if style == "garden":
        primary = ARTWORK_ROOT / "Generated-quality-reference-v4-pixar-moonlit-garden.png"
    else:
        primary = ARTWORK_ROOT / "Generated-quality-reference-v5-pixar-basket-bedtime.png"
    refs = [
        primary,
        ARTWORK_ROOT / "Universe-core-cast-turnaround-sheet.png",
        ARTWORK_ROOT / "Dolly" / "Dolly-character-expression-board.png",
        ARTWORK_ROOT / "Daphne" / "Daphne-character-expression-board.png",
    ]
    missing = [path for path in refs if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing reference files: {missing}")
    return refs


def _generate_image(prompt: str, *, style: str) -> bytes:
    if not ILLUSTRATION_GENERATION_API_KEY:
        raise RuntimeError("ILLUSTRATION_GENERATION_API_KEY is not configured")
    refs = _reference_paths(style)
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


def _next_cover_path() -> tuple[str, Path]:
    folder = get_local_asset_path("mock-assets/images/generated/story-3")
    folder.mkdir(parents=True, exist_ok=True)
    version = 1
    while True:
        relative = f"mock-assets/images/generated/story-3/cover-v{version}.png"
        local = get_local_asset_path(relative)
        if not local.exists():
            return f"/{relative}", local
        version += 1


def _update_cover(conn: sqlite3.Connection, *, prompt: str) -> str:
    image_bytes = _generate_image(prompt, style="garden")
    public_url, local_path = _next_cover_path()
    local_path.write_bytes(image_bytes)
    conn.execute(
        """
        UPDATE bookpage
        SET image_url = ?, updated_at = CURRENT_TIMESTAMP
        WHERE book_id = ? AND page_number = 0
        """,
        (public_url, BOOK_ID),
    )
    conn.commit()
    return public_url


def _update_story_page(conn: sqlite3.Connection, *, page_number: int, prompt: str, style: str) -> str:
    image_bytes = _generate_image(prompt, style=style)
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
        (prompt, "image_generated", public_url, story_page_id),
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
            prompt,
            public_url,
            version_number,
            "generated",
            "openai",
            None,
            "Regenerated after user review for sequence relevance",
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
      Updated local preview after user-review illustration fixes for sequence and cover/page-1 visibility.
    </div>
{''.join(sections)}
  </div>
</body>
</html>
"""
    PREVIEW_HTML.write_text(html, encoding="utf-8")


def main() -> None:
    cover_prompt = """
Create a high-end Pixar-style animated storybook cover illustration.

Scene:
An inviting opening bedtime scene. Verity stands by an open window with Dolly and Daphne beside her, all looking out toward a magical moonlit garden while Buddybug glows above them like a tiny lantern.

Story relevance:
This is the beginning of the bedtime adventure. Nobody is asleep yet, nobody is tucked into bed yet, and the image should feel like the story is just about to begin.

Characters:
Verity with long golden blonde hair and a soft white dress.
Dolly as a gentle grey dapple dachshund with a blue collar.
Daphne as a black-and-tan dachshund with a red collar and gold star tag.
Buddybug as a small glowing golden firefly.

Environment:
Warm bedroom window light in the foreground, moonlit garden with flowers and a deep blue sky beyond, cozy but adventurous bedtime atmosphere.

Composition:
Vertical cover composition, clear full-character grouping, strong focal glow, welcoming opening image, and clean space in the upper area for a title treatment.

Negative requirements:
No bedtime tuck-in pose, no sleeping, no blanket wrapped around the dogs, no reading chair close-up.
""".strip()

    page_1_prompt = """
Create one children's storybook illustration for a single story page.

Page number: 1
Scene location: by the window
Characters present: Verity, Dolly, Daphne, Buddybug.
Key action: Verity pauses by the window with Dolly and Daphne while Buddybug glows nearby and the moonlit garden calls them onward.
Emotional tone: opening bedtime wonder, calm curiosity, gentle anticipation.
Important objects: window, moonlit garden, flowers, warm window glow.
Time of day and lighting: warm bedroom light on the characters with cool moonlight outside and Buddybug's soft golden glow.
Composition note: opening scene composition with the characters grouped at the window and the moonlit garden clearly visible beyond them.

Story relevance:
This is the start of the adventure, before anyone goes to bed. The image should feel like they are noticing the garden and getting ready to continue.

Negative prompt:
no tucked-in pose; no blanket covering the dogs; no sleeping; no basket bed; no reading-chair bedtime ending scene.
""".strip()

    page_4_prompt = """
Create one children's storybook illustration for a single story page.

Page number: 4
Scene location: moonlit garden
Characters present: Verity, Dolly, Daphne.
Key action: In the moonlit garden, Verity kneels among the flowers and shares a quiet reassuring smile with Dolly while Daphne stays close beside them.
Emotional tone: calm reassurance, gentle connection, mid-adventure comfort.
Important objects: moonlit flowers, garden path, soft night glow.
Time of day and lighting: soft moonlight with warm magical highlights and no indoor bedtime props.
Composition note: close comforting outdoor composition with one caring gesture and both dogs clearly present beside Verity.

Story relevance:
This page must stay before the later return-to-bed ending. They are still outside in the garden and still mid-story.

Negative prompt:
no bed; no basket; no blanket wrapped around Dolly; no tucked-in pose; no sleeping; no indoor bedroom scene.
""".strip()

    page_6_prompt = """
Create one children's storybook illustration for a single story page.

Page number: 6
Scene location: moonlit garden
Characters present: Verity, Dolly, Daphne.
Key action: Verity, Dolly, and Daphne pause together on the moonlit garden path, listening to the breeze and the soft night sounds around them.
Emotional tone: peaceful listening pause, calm wonder, gentle outdoor stillness.
Important objects: moonlit path, flowers, leaves, soft night glow.
Time of day and lighting: moonlit garden lighting with subtle warm magical highlights, entirely outdoors.
Composition note: quiet outdoor cluster composition with listening body language and the garden path clearly readable.

Story relevance:
They are still in the garden at this point. The image should feel like a calm outdoor pause before the final return to bed.

Negative prompt:
no blanket; no bed; no tucked-in pose; no sleeping; no pillows; no indoor bedroom props.
""".strip()

    conn = sqlite3.connect(ROOT / "buddybug.db")
    try:
        print("Regenerating cover...", flush=True)
        print(_update_cover(conn, prompt=cover_prompt), flush=True)
        print("Regenerating page 1...", flush=True)
        print(_update_story_page(conn, page_number=1, prompt=page_1_prompt, style="bedroom"), flush=True)
        print("Regenerating page 4...", flush=True)
        print(_update_story_page(conn, page_number=4, prompt=page_4_prompt, style="garden"), flush=True)
        print("Regenerating page 6...", flush=True)
        print(_update_story_page(conn, page_number=6, prompt=page_6_prompt, style="garden"), flush=True)
        _rebuild_preview_html(conn)
        print(f"Updated preview: {PREVIEW_HTML}", flush=True)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
