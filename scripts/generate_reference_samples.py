from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
import sys

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import ILLUSTRATION_GENERATION_API_KEY, ILLUSTRATION_GENERATION_BASE_URL

ARTWORK_ROOT = Path(r"C:\Users\User\Documents\BuddyBug\Artwork\BuddyBug Character Bible")


def _to_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _generate(output_name: str, prompt: str, reference_paths: list[Path]) -> Path:
    payload = {
        "model": "gpt-image-1.5",
        "prompt": prompt,
        "images": [{"image_url": _to_data_url(path)} for path in reference_paths],
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
    output_path = ARTWORK_ROOT / output_name
    output_path.write_bytes(base64.b64decode(response.json()["data"][0]["b64_json"]))
    return output_path


def main() -> None:
    cast_refs = [
        ARTWORK_ROOT / "Verity" / "Verity-storylight-style-board.png",
        ARTWORK_ROOT / "Daphne" / "Daphne-character-expression-board.png",
        ARTWORK_ROOT / "Dolly" / "Dolly-character-expression-board.png",
        ARTWORK_ROOT / "BuddyBug" / "BuddyBug-character-expression-board.png",
    ]
    turnaround_refs = [
        ARTWORK_ROOT / "Universe-core-cast-turnaround-sheet.png",
        ARTWORK_ROOT / "Verity" / "Verity-storylight-style-board.png",
        ARTWORK_ROOT / "Daphne" / "Daphne-character-expression-board.png",
        ARTWORK_ROOT / "Dolly" / "Dolly-character-expression-board.png",
    ]

    prompt_a = """Create a warm children's storybook illustration in a soft watercolor and storybook animation style.

Style:
dreamy watercolor children's book illustration, soft painterly textures, hand-painted feel, gentle gradients, subtle paper grain, warm golden highlights, delicate linework, glowing magical accents.

Lighting:
soft bedtime lighting with warm golden glow, gentle moonlight through a window, subtle magical firefly light, warm lamp glow, cozy nighttime atmosphere.

Colour palette:
warm golds, soft creams, pale blues, dusty lavender, gentle greens, warm amber highlights, pastel night tones.

Characters (must match reference library exactly):
Verity - young blonde woman with big expressive eyes, warm smile, soft flowing hair, white dress.
Daphne - black and tan dachshund, red collar with gold star tag, playful expression.
Dolly - grey dapple dachshund, blue collar, gentle expression.
Buddybug - glowing golden firefly with friendly face and soft magical light.

Composition:
storybook composition, medium-close framing, characters centered and slightly forward, cozy environment surrounding them, shallow depth feeling, magical atmosphere, gentle background details.

Mood:
cozy bedtime, calm, magical, comforting, safe, dreamy.

Environment:
soft storybook setting with flowers, blankets, warm bedroom lighting, moon visible through window, subtle glowing particles and fireflies.

Rendering:
high detail watercolor illustration, professional children's book quality, soft edges, luminous highlights, cinematic warmth, painterly brushwork.

Aspect:
vertical illustration suitable for storybook page.
"""

    prompt_b = """Create a warm children's storybook illustration in a soft watercolor and storybook animation style.

Style:
dreamy watercolor children's book illustration, soft painterly textures, hand-painted feel, gentle gradients, subtle paper grain, warm golden highlights, delicate linework, glowing magical accents.

Lighting:
soft bedtime lighting with warm golden glow, gentle moonlight through a window, subtle magical firefly light, warm lamp glow, cozy nighttime atmosphere.

Characters (must match reference library exactly):
Verity - young blonde woman with big expressive eyes, warm smile, soft flowing hair, white dress.
Daphne - black and tan dachshund, red collar with gold star tag, playful expression.
Dolly - grey dapple dachshund, blue collar, gentle expression.
Buddybug - glowing golden firefly with friendly face and soft magical light.

Composition:
storybook composition, medium-close framing, characters centered and slightly forward, cozy environment surrounding them.

Mood:
cozy bedtime, calm, magical, comforting, safe, dreamy.

Environment:
soft storybook setting with flowers and moonlit glow.

Rendering:
professional children's book quality, luminous highlights, painterly brushwork, crisp facial clarity, crisp collars and coat markings, and readable silhouettes without becoming harsh or realistic.

Aspect:
vertical illustration suitable for storybook page.
"""

    prompt_c = """Create a high-end Pixar-style animated illustration.

Scene:
A cozy nighttime bedtime moment. A young blonde woman named Verity sits in a soft woven basket chair with a warm blanket while reading an open storybook. Two dachshunds sit beside her listening to the story.

Characters:
Verity - young woman with long golden blonde hair, large expressive Pixar-style eyes, warm smile, wearing a soft white dress.

Daphne - small black and tan dachshund with large expressive eyes, wearing a red collar with a gold star tag.

Dolly - small grey dapple dachshund with big expressive eyes and a blue collar.

Buddybug - a small glowing golden firefly with a friendly face hovering above the book, softly illuminating the pages.

Environment:
A cozy bedroom with a large window behind them. The window reveals a deep blue night sky with a glowing crescent moon and twinkling stars. Soft curtains frame the window and flowers grow outside the glass. A warm bedside lamp glows on a small table beside the chair.

Lighting:
Pixar-style cinematic lighting with warm golden lamp light and soft blue moonlight entering from the window. Buddybug emits a gentle magical glow that lights the storybook pages.

Composition:
Medium close-up storybook composition. Verity centered holding the open book, the two dachshunds leaning toward the book on each side. Buddybug hovering just above the pages. Cozy blanket and basket chair filling the foreground.

Mood:
Magical, warm, peaceful bedtime storytelling moment.

Style:
Pixar-style 3D animation rendering, ultra-detailed character expressions, soft cinematic lighting, warm color palette, high-quality animated film aesthetic.
"""

    prompt_d = """Create a high-end Pixar-style animated illustration.

Scene:
A magical moonlit garden storytelling moment. Verity sits on a soft blanket in a flower garden at night with an open glowing storybook in her lap. Daphne stands eagerly on one side, Dolly sits calmly on the other, and Buddybug hovers above the pages.

Characters:
Verity - young woman with long golden blonde hair, large expressive Pixar-style eyes, warm smile, wearing a soft white dress.

Daphne - small black and tan dachshund with large expressive eyes, wearing a red collar with a gold star tag.

Dolly - small grey dapple dachshund with big expressive eyes and a blue collar.

Buddybug - a small glowing golden firefly with a friendly face hovering above the book, softly illuminating the pages.

Environment:
A moonlit flower garden filled with daisies, soft glowing particles, and a dreamy crescent moon in a deep blue sky. Gentle foliage frames the scene and the book casts warm golden light onto the characters.

Lighting:
Pixar-style cinematic lighting with soft moonlight, warm magical glow from the book, and Buddybug adding a subtle golden rim light.

Composition:
Vertical storybook composition, medium shot. Verity centered, the dachshunds close to her on each side, Buddybug above the book, flowers and night sky surrounding them.

Mood:
Magical, warm, peaceful bedtime storytelling moment.

Style:
Pixar-style 3D animation rendering, ultra-detailed character expressions, soft cinematic lighting, warm color palette, high-quality animated film aesthetic.
"""

    prompt_e = """Create a high-end Pixar-style animated illustration.

Scene:
A cozy bedtime basket scene. Verity sits beside a large woven basket bed indoors, reading a glowing storybook while Daphne rests happily near the open pages and Dolly curls gently inside the basket. Buddybug hovers above the book like a tiny lantern.

Characters:
Verity - young woman with long golden blonde hair, large expressive Pixar-style eyes, warm smile, wearing a soft white dress.

Daphne - small black and tan dachshund with large expressive eyes, wearing a red collar with a gold star tag.

Dolly - small grey dapple dachshund with big expressive eyes and a blue collar.

Buddybug - a small glowing golden firefly with a friendly face hovering above the book, softly illuminating the pages.

Environment:
A warm storybook bedroom with soft curtains, moonlight coming through a window, a glowing bedside lamp, blankets, flowers visible outside, and a woven basket bed filling the foreground.

Lighting:
Pixar-style cinematic lighting with warm lamp glow, cool blue moonlight through the window, and Buddybug casting magical golden light across the book and basket.

Composition:
Vertical storybook composition, medium-close framing. Verity and the book are central, Daphne leans toward the pages, Dolly nestles comfortably in the basket, and Buddybug glows just above the storybook.

Mood:
Comforting, magical, safe, cozy bedtime storytelling.

Style:
Pixar-style 3D animation rendering, ultra-detailed character expressions, soft cinematic lighting, warm color palette, high-quality animated film aesthetic.
"""

    first = _generate("Generated-quality-reference-v1.png", prompt_a, cast_refs)
    second = _generate("Generated-quality-reference-v2.png", prompt_b, turnaround_refs)
    third = _generate("Generated-quality-reference-v3-pixar.png", prompt_c, cast_refs)
    fourth = _generate("Generated-quality-reference-v4-pixar-moonlit-garden.png", prompt_d, cast_refs)
    fifth = _generate("Generated-quality-reference-v5-pixar-basket-bedtime.png", prompt_e, cast_refs)
    print(first)
    print(second)
    print(third)
    print(fourth)
    print(fifth)


if __name__ == "__main__":
    main()
