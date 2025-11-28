from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI(title="Bedtime Stories API")

# Allow requests from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StoryRequest(BaseModel):
    child_name: str
    favourite_thing: str
    style: str = "gentle"   # gentle, silly, adventurous
    length: str = "short"   # short, medium, long
    siblings: str | None = None  # comma-separated sibling names from the frontend


class StoryResponse(BaseModel):
    story: str


@app.get("/health")
def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok"}


# -------- story helpers -------- #

SLEEPY_OPENERS = [
    "Once upon a very calm night,",
    "On a quiet night when the moon looked extra soft,",
    "One sleepy evening, just before bedtime,",
]

GENTLE_SETTINGS = [
    "the sky was full of sleepy stars.",
    "a tiny breeze was whispering around the houses.",
    "the world outside the window was hushed and still.",
]

SILLY_TWISTS = [
    "which was quite surprising for a Tuesday.",
    "and even the pillows giggled a little.",
    "and the slippers decided to dance for no reason at all.",
]

ADVENTURE_HOOKS = [
    "when a tiny, twinkly light tapped on the window.",
    "when a soft knock came from under the bed (a friendly one, of course).",
    "when a little map rolled itself open on the pillow.",
]

CLOSERS = [
    "And as their eyes grew heavier and heavier, the night wrapped them in a cosy, quiet hug.",
    "By the time the moon had climbed a little higher, everyone felt warm, safe, and ready to dream.",
    "Soon the whole room was filled with sleepy breaths and soft dreams, and the stars watched over them all.",
]


def make_intro(name: str, siblings: list[str], style: str) -> str:
    opener = random.choice(SLEEPY_OPENERS)
    setting = random.choice(GENTLE_SETTINGS)

    if siblings:
        sib_text = ", ".join(siblings)
        family_bit = f"{name} and {sib_text}"
    else:
        family_bit = name

    line = f"{opener} there was a child named {family_bit}."
    line += " " + setting

    if style == "silly":
        line += " " + random.choice(SILLY_TWISTS)
    elif style == "adventurous":
        line += " " + random.choice(ADVENTURE_HOOKS)

    return line


def make_middle(name: str, siblings: list[str], favourite: str, style: str) -> str:
    if style == "silly":
        return (
            f"{name} couldn't stop giggling about {favourite}. "
            f"Every time they tried to stay serious, {favourite} popped into their head wearing tiny socks."
        )

    if style == "adventurous":
        partner = f"{' and '.join(siblings)} " if siblings else ""
        return (
            f"{name}{(' and ' + ' and '.join(siblings)) if siblings else ''} "
            f"decided to follow a gentle, glowing path made of {favourite}. "
            f"It never went anywhere scary, only to places where the air felt warm and safe."
        )

    # gentle default
    return (
        f"{name} thought about {favourite} and felt a little glow in their chest. "
        f"In their mind, {favourite} always lived in a soft, quiet place where nothing bad ever happened."
    )


def make_extra_details(favourite: str) -> str:
    details = [
        f"Sometimes {favourite} appeared in their dreams, but always in soft colours and slow, floaty movements.",
        f"Outside, the night seemed to hum the same gentle rhythm as their breathing.",
        f"The room felt like a little nest, with blankets, pillows, and the quiet idea of {favourite} keeping watch.",
    ]
    return random.choice(details)


def build_story(data: StoryRequest) -> str:
    # Normalise / defaults
    name = data.child_name.strip() or "someone special"
    favourite = data.favourite_thing.strip() or "something they loved very much"

    siblings: list[str] = []
    if data.siblings:
        siblings = [s.strip() for s in data.siblings.split(",") if s.strip()]

    # Decide how many paragraphs
    if data.length == "short":
        paragraphs = 2
    elif data.length == "medium":
        paragraphs = 3
    else:
        paragraphs = 4

    intro = make_intro(name, siblings, data.style)
    middle = make_middle(name, siblings, favourite, data.style)
    extra = make_extra_details(favourite)
    closer = random.choice(CLOSERS)

    all_parts = [intro, middle, extra, closer]
    # Trim to desired length
    selected = all_parts[:paragraphs]

    return "\n\n".join(selected)


# -------- endpoints -------- #

@app.post("/story", response_model=StoryResponse)
def create_story(req: StoryRequest) -> StoryResponse:
    story_text = build_story(req)
    return StoryResponse(story=story_text)
