from app.schemas.story_engine_schema import StoryHook


BEDTIME_MODE = "bedtime"
STANDARD_MODE = "standard"

DEFAULT_BEDTIME_TONE = "warm, plot-led, gently playful, bedtime-safe, concrete visible bedtime progression, sleepy by the ending"
DEFAULT_STANDARD_TONE = "warm, playful, cheeky, plot-led"
DEFAULT_ADVENTURE_TONE = "warm, adventurous, witty, cheeky, mischievous, giggly, plot-led, engaging and funny"

BEDTIME_SETTINGS = [
    "cozy bedroom",
    "quiet garden path",
    "storybook clearing",
    "soft lamp-lit hallway",
    "sleepy meadow",
]
STANDARD_3_7_SETTINGS = [
    "breakfast kitchen",
    "garden path",
    "reading nook",
    "puddle-side picnic",
    "toy cupboard",
]
ADVENTURE_SETTINGS = [
    "secret library",
    "hidden garden",
    "puzzle-filled forest path",
    "moonlit observatory",
    "starlit map room",
]

BEDTIME_THEMES = [
    "kindness",
    "sharing",
    "bravery",
    "calmness",
    "curiosity",
    "bedtime routine",
    "feeling safe at night",
    "saying goodnight",
]
STANDARD_3_7_THEMES = [
    "kindness",
    "sharing",
    "curiosity",
    "friendship",
    "problem solving",
    "responsibility",
    "teamwork",
]
ADVENTURE_THEMES = [
    "teamwork",
    "problem solving",
    "courage",
    "curiosity",
    "friendship",
    "responsibility",
    "hope",
]

BEDTIME_FEELINGS = ["sleepy", "reassured", "peaceful", "comforted", "calm", "settled"]
STANDARD_3_7_FEELINGS = ["pleased", "cheerful", "relieved", "proud", "cozy", "glad"]
ADVENTURE_FEELINGS = ["encouraged", "inspired", "brave", "hopeful", "curious", "proud"]

BEDTIME_MINUTES = [5, 6, 7, 8]
STANDARD_3_7_MINUTES = [5, 6, 7, 8]
ADVENTURE_MINUTES = [7, 8, 9, 10]

CHARACTER_BEHAVIOUR = {
    "Verity": {
        "role": "calm mother figure",
        "guidance": "kind, grounding presence who gently helps solve things",
        "preferred_hooks": ["gentle_problem", "misunderstanding", "missing_item"],
    },
    "Dolly": {
        "role": "thoughtful gentle friend",
        "guidance": "emotionally warm, slightly cautious, kind-hearted",
        "preferred_hooks": ["missing_item", "gentle_problem", "tiny_creature_problem"],
    },
    "Daphne": {
        "role": "cheeky playful catalyst",
        "guidance": "confident, slightly overestimates herself, funny troublemaker energy",
        "preferred_hooks": ["clever_shortcut", "accidental_mess", "helpful_plan_goes_wrong", "silly_competition"],
    },
    "Buddybug": {
        "role": "warm magical helper",
        "guidance": "observant glowy guide who notices what others miss",
        "preferred_hooks": ["unexpected_discovery", "misunderstanding", "tiny_creature_problem"],
    },
    "Glowmoth": {
        "role": "storylight guardian helper",
        "guidance": "soft magical support who helps keep the mood friendly",
        "preferred_hooks": ["unexpected_discovery", "gentle_problem"],
    },
    "Twinklet": {
        "role": "storylight guardian helper",
        "guidance": "playful and light, good for small helpful surprises",
        "preferred_hooks": ["pretend_game", "unexpected_discovery"],
    },
    "Whisperwing": {
        "role": "storylight guardian helper",
        "guidance": "guiding presence for safe, calm mysteries",
        "preferred_hooks": ["missing_item", "gentle_problem", "unexpected_discovery"],
    },
}

HOOK_DEFINITIONS = {
    "missing_item": StoryHook(
        key="missing_item",
        description="Something important but child-sized has gone missing.",
        typical_tone="gentle, curious, reassuring",
        bedtime_mode_allowed=True,
        standard_mode_allowed=True,
        example_plot_directions=[
            "A blanket, ribbon, lantern, or snack cannot be found.",
            "The friends search in the wrong place first.",
            "The solution comes from patience and noticing a clue.",
        ],
    ),
    "clever_shortcut": StoryHook(
        key="clever_shortcut",
        description="Someone takes a shortcut that turns into a mild muddle.",
        typical_tone="cheeky, playful, lightly mischievous",
        bedtime_mode_allowed=False,
        standard_mode_allowed=True,
        example_plot_directions=[
            "Daphne proudly suggests a quicker way.",
            "The shortcut leaves everyone muddy, leafy, or turned around.",
            "They laugh and fix the muddle kindly.",
        ],
    ),
    "accidental_mess": StoryHook(
        key="accidental_mess",
        description="A harmless mess creates a funny problem to solve.",
        typical_tone="playful, giggly, kind",
        bedtime_mode_allowed=False,
        standard_mode_allowed=True,
        example_plot_directions=[
            "A splash, tumble, or dropped basket makes a safe mess.",
            "Helping makes the mess a little bigger before it gets better.",
            "Cleaning up becomes part of the fun.",
        ],
    ),
    "tiny_creature_problem": StoryHook(
        key="tiny_creature_problem",
        description="A very small creature needs help or causes a tiny problem.",
        typical_tone="gentle, warm, observant",
        bedtime_mode_allowed=True,
        standard_mode_allowed=True,
        example_plot_directions=[
            "A frog, moth, mouse, or beetle has taken the wrong thing.",
            "The characters must help without scaring it.",
            "The ending is kind and satisfying.",
        ],
    ),
    "misunderstanding": StoryHook(
        key="misunderstanding",
        description="A funny wrong assumption creates a small plot problem.",
        typical_tone="warm, story-led, lightly funny",
        bedtime_mode_allowed=True,
        standard_mode_allowed=True,
        example_plot_directions=[
            "Two friends think the same thing for different reasons.",
            "The mix-up sends them briefly the wrong way.",
            "The explanation lands softly and clearly.",
        ],
    ),
    "helpful_plan_goes_wrong": StoryHook(
        key="helpful_plan_goes_wrong",
        description="A sensible plan starts well and then becomes a little muddle.",
        typical_tone="playful, capable, child-friendly",
        bedtime_mode_allowed=False,
        standard_mode_allowed=True,
        example_plot_directions=[
            "Someone tries to help quickly.",
            "The helper accidentally makes the problem bigger first.",
            "The group fixes it together without blame.",
        ],
    ),
    "silly_competition": StoryHook(
        key="silly_competition",
        description="A small contest or boast turns into a funny plot beat.",
        typical_tone="cheeky, giggly, upbeat",
        bedtime_mode_allowed=False,
        standard_mode_allowed=True,
        example_plot_directions=[
            "The characters compare hops, jumps, or balancing skills.",
            "The competition gets interrupted by a harmless mistake.",
            "They end up sharing the win or changing the game.",
        ],
    ),
    "unexpected_discovery": StoryHook(
        key="unexpected_discovery",
        description="The story starts when someone notices something odd or surprising.",
        typical_tone="curious, warm, gently magical",
        bedtime_mode_allowed=True,
        standard_mode_allowed=True,
        example_plot_directions=[
            "Buddybug notices something glowing in the wrong place.",
            "The clue leads to a safe mystery.",
            "The answer reveals a kind or funny truth.",
        ],
    ),
    "pretend_game": StoryHook(
        key="pretend_game",
        description="A pretend game leads to an unexpected but gentle story problem.",
        typical_tone="playful, imaginative, warm",
        bedtime_mode_allowed=False,
        standard_mode_allowed=True,
        example_plot_directions=[
            "A game starts as pretend and causes a real muddle.",
            "The characters have to switch from pretending to problem solving.",
            "The ending keeps the fun while restoring order.",
        ],
    ),
    "gentle_problem": StoryHook(
        key="gentle_problem",
        description="A small everyday problem needs calm observation and teamwork.",
        typical_tone="calm, plot-led, reassuring",
        bedtime_mode_allowed=True,
        standard_mode_allowed=True,
        example_plot_directions=[
            "Something is out of order just before bed.",
            "The characters work through one clue at a time.",
            "The resolution brings the routine back into place.",
        ],
    ),
}

BEDTIME_ALLOWED_HOOK_KEYS = [
    "missing_item",
    "tiny_creature_problem",
    "misunderstanding",
    "gentle_problem",
    "unexpected_discovery",
]

STANDARD_ALLOWED_HOOK_KEYS = [
    "accidental_mess",
    "clever_shortcut",
    "helpful_plan_goes_wrong",
    "silly_competition",
    "pretend_game",
    "misunderstanding",
    "unexpected_discovery",
    "missing_item",
]
