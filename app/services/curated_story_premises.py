"""Curated one-line premises for Buddybug stories (avoids template repetition).

Indexed 0–99 in ten thematic blocks of ten, matching editorial categories.
"""

from __future__ import annotations

from app.services.story_engine_data import BEDTIME_MODE, STANDARD_MODE

CURATED_PREMISES: list[str] = [
    # Missing things (1–10)
    "Dolly's blanket disappears just before bedtime.",
    "Daphne loses her shiny star tag somewhere in the garden.",
    "Buddybug's glow suddenly becomes very dim.",
    "Verity cannot find her favourite storybook.",
    "A basket of apples goes missing from the porch.",
    "Dolly's favourite blue ball rolls away.",
    "Daphne's squeaky toy vanishes mysteriously.",
    "Someone has taken all the carrots from the garden.",
    "The lantern light suddenly goes out.",
    "A trail of leaves leads to something missing.",
    # Clever plans that go wrong (11–20)
    "Daphne insists she knows a faster way to the pond.",
    "Buddybug tries to help guide everyone through the garden at night.",
    "Dolly tries to build the perfect leaf pile.",
    "Daphne tries to dig the biggest hole ever.",
    "Buddybug tries to light up the entire garden.",
    "Dolly attempts to build a bridge over a puddle.",
    "Daphne creates a shortcut through the bushes.",
    "Buddybug tries to organize a firefly parade.",
    "Dolly tries to hide a surprise for Verity.",
    "Daphne tries to jump the widest puddle.",
    # Funny accidents (21–30)
    "Daphne slips into the pond.",
    "Dolly gets covered in leaves while rolling down a hill.",
    "Buddybug bumps into a lantern and spins around.",
    "A bucket of water tips over unexpectedly.",
    "Daphne gets tangled in a blanket.",
    "Dolly accidentally splashes mud everywhere.",
    "Buddybug glows so brightly everyone is dazzled.",
    "A pile of apples rolls across the garden.",
    "Daphne gets stuck in a bush.",
    "Dolly slides down a muddy path.",
    # Tiny creature trouble (31–40)
    "A frog sits inside Dolly's basket.",
    "A hedgehog curls up inside a blanket.",
    "A snail crawls onto Daphne's nose.",
    "A squirrel steals a shiny object.",
    "A butterfly refuses to leave the porch.",
    "A beetle rolls something strange across the path.",
    "A bird drops a mysterious feather.",
    "A caterpillar crawls into the storybook.",
    "A family of ants marches across the garden.",
    "A ladybird lands on Buddybug.",
    # Misunderstandings (41–50)
    "Dolly thinks someone took her toy.",
    "Daphne believes she heard a monster in the bushes.",
    "Buddybug thinks a lantern is another firefly.",
    "Dolly thinks the moon is following her.",
    "Daphne believes a shadow is chasing her.",
    "Buddybug mistakes a flower for a glowing bug.",
    "Dolly thinks the wind is whispering to her.",
    "Daphne thinks the frog is trying to talk.",
    "Buddybug thinks a falling leaf is flying.",
    "Dolly thinks someone is hiding nearby.",
    # Rainy day stories (51–60)
    "Rain starts just as everyone plans a garden game.",
    "Dolly and Daphne look for indoor adventures.",
    "Buddybug tries to light up a dark rainy afternoon.",
    "Verity brings out a mysterious old storybook.",
    "The rain forms giant puddles everywhere.",
    "Dolly watches raindrops race down a window.",
    "Daphne jumps in puddles one by one.",
    "Buddybug glows inside a cosy blanket fort.",
    "Verity makes warm cocoa for everyone.",
    "The rain reveals something hidden in the garden.",
    # Curiosity stories (61–70)
    "Buddybug notices a strange glowing object.",
    "Daphne finds a tiny hidden path.",
    "Dolly discovers something buried under leaves.",
    "A strange sound comes from the garden shed.",
    "Buddybug spots something sparkling in the grass.",
    "Dolly sees a mysterious footprint.",
    "Daphne finds a shiny button.",
    "A trail of petals leads somewhere new.",
    "Buddybug sees a tiny light flicker in the bushes.",
    "Dolly hears something rustling softly.",
    # Friendly challenges (71–80)
    "Dolly and Daphne see who can find the biggest leaf.",
    "Buddybug challenges everyone to a glow race.",
    "Dolly and Daphne try to build the tallest leaf tower.",
    "Buddybug organizes a hide-and-seek game.",
    "Daphne competes to jump the most puddles.",
    "Dolly tries to collect the prettiest flowers.",
    "Buddybug challenges everyone to find the brightest glow.",
    "Daphne attempts the longest hop.",
    "Dolly builds the cosiest blanket nest.",
    "Buddybug leads a nighttime treasure hunt.",
    # Magical garden moments (81–90)
    "Buddybug discovers glowing mushrooms.",
    "The fireflies gather for a dance.",
    "The garden glows brighter than usual tonight.",
    "Buddybug leads everyone to a secret clearing.",
    "Dolly discovers a hidden lantern.",
    "A mysterious glow appears behind the apple tree.",
    "The stars seem extra bright tonight.",
    "Buddybug invites everyone to a firefly parade.",
    "A hidden path appears in the moonlight.",
    "The garden feels different tonight.",
    # Silly situations (91–100)
    "Daphne gets leaves stuck all over her ears.",
    "Dolly tries to balance apples on her nose.",
    "Buddybug accidentally glows too brightly.",
    "Daphne gets covered in mud while digging.",
    "Dolly trips over a pile of sticks.",
    "Buddybug spins around like a tiny lantern.",
    "Daphne accidentally scares herself.",
    "Dolly gets tangled in a blanket.",
    "Buddybug leads everyone in circles.",
    "Daphne insists she can jump the biggest puddle.",
]


def curated_hook_for_index(premise_index: int, *, mode: str) -> str:
    """Map premise block (0–9) to a pipeline hook type valid for the story mode."""
    block = min(premise_index // 10, 9)
    if mode == BEDTIME_MODE:
        by_block = [
            "missing_item",
            "gentle_problem",
            "gentle_problem",
            "tiny_creature_problem",
            "misunderstanding",
            "gentle_problem",
            "unexpected_discovery",
            "gentle_problem",
            "unexpected_discovery",
            "gentle_problem",
        ]
    elif mode == STANDARD_MODE:
        by_block = [
            "missing_item",
            "helpful_plan_goes_wrong",
            "accidental_mess",
            "unexpected_discovery",
            "misunderstanding",
            "unexpected_discovery",
            "unexpected_discovery",
            "silly_competition",
            "unexpected_discovery",
            "silly_competition",
        ]
    else:
        by_block = [
            "gentle_problem",
            "gentle_problem",
            "gentle_problem",
            "unexpected_discovery",
            "misunderstanding",
            "gentle_problem",
            "unexpected_discovery",
            "gentle_problem",
            "unexpected_discovery",
            "gentle_problem",
        ]
    return by_block[block]


def title_from_curated_premise(premise: str, *, max_len: int = 56) -> str:
    """Short title from the premise line (no LLM)."""
    base = premise.strip().rstrip(".")
    if len(base) <= max_len:
        return base
    cut = base[: max_len - 1].rsplit(" ", 1)[0]
    return f"{cut}…"
