from sqlmodel import Session, select

from app.models import Character


CANONICAL_CHARACTERS: list[dict[str, str | bool | None]] = [
    {
        "name": "Verity",
        "role": "main character",
        "species": "human",
        "short_description": "A kind young mother figure who reads and watches over bedtime stories.",
        "visual_description": "Young woman with long golden-blonde hair, warm brown eyes, a gentle smile, a simple white dress, and expressive but natural cartoon eyes in a soft watercolor bedtime storybook style.",
        "personality_traits": "kind, nurturing, calm, gentle, warm",
        "style_rules": "Soft watercolor/cartoon bedtime illustration, rounded friendly shapes, warm moonlit lighting, expressive but not exaggerated eyes, gentle storybook atmosphere.",
        "color_palette": "cream white, warm gold, soft beige",
        "accessories": "none",
        "age_group": "3-7",
        "is_active": True,
    },
    {
        "name": "Daphne",
        "role": "main character",
        "species": "dachshund",
        "short_description": "A playful black-and-tan dachshund with a bright bedtime story presence.",
        "visual_description": "Black-and-tan dachshund with tan eyebrows, tan muzzle, tan chest and legs, expressive cartoon eyes, a red collar, and a gold star tag, shown in a soft watercolor bedtime storybook style.",
        "personality_traits": "playful, curious, adventurous, energetic, loving",
        "style_rules": "Soft watercolor/cartoon bedtime illustration, rounded dachshund shapes, expressive but not exaggerated eyes, warm moonlit glow, gentle storybook look.",
        "color_palette": "black, tan, warm red, soft gold",
        "accessories": "red collar with gold star tag",
        "age_group": "3-7",
        "is_active": True,
    },
    {
        "name": "Dolly",
        "role": "main character",
        "species": "dachshund",
        "short_description": "A calm grey dachshund with a thoughtful and gentle nature.",
        "visual_description": "Grey dachshund with a soft coat, expressive cartoon eyes, a blue collar, and a gentle face in a soft watercolor bedtime storybook style.",
        "personality_traits": "calm, thoughtful, gentle, caring, loyal",
        "style_rules": "Soft watercolor/cartoon bedtime illustration, rounded dachshund shapes, expressive but not exaggerated eyes, warm bedtime atmosphere, gentle storybook look.",
        "color_palette": "soft grey, dusty blue, cream highlights",
        "accessories": "blue collar",
        "age_group": "3-7",
        "is_active": True,
    },
    {
        "name": "Buddybug",
        "role": "guardian",
        "species": "firefly",
        "short_description": "A glowing golden firefly who watches over stories as the Story Keeper.",
        "visual_description": "Small glowing golden firefly with a round friendly face, tiny sparkling wings, and a warm magical light in a soft watercolor bedtime storybook style.",
        "personality_traits": "cheerful, curious, magical, friendly, encouraging",
        "style_rules": "Soft watercolor/cartoon bedtime illustration, tiny rounded magical form, warm glow, gentle sparkles, calming storybook atmosphere.",
        "color_palette": "warm gold, soft yellow, pale amber",
        "accessories": "none",
        "age_group": "3-7",
        "is_active": True,
    },
    {
        "name": "Glowmoth",
        "role": "guardian",
        "species": "moth",
        "short_description": "A pale blue moth who helps little ones feel calm and sleepy.",
        "visual_description": "Soft glowing pale blue moth with wide velvet wings, sleepy gentle eyes, and a soothing magical shimmer in a soft watercolor bedtime storybook style.",
        "personality_traits": "soothing, patient, calm, gentle, peaceful",
        "style_rules": "Soft watercolor/cartoon bedtime illustration, soft wing edges, cool calming glow, rounded gentle features, quiet bedtime magic.",
        "color_palette": "pale blue, silver blue, misty white",
        "accessories": "none",
        "age_group": "3-7",
        "is_active": True,
    },
    {
        "name": "Twinklet",
        "role": "guardian",
        "species": "star-bug",
        "short_description": "A tiny bright star-like bug who discovers new bedtime adventures.",
        "visual_description": "Small bright star-shaped glowing bug with tiny fluttering wings, playful sparkles, and a lively magical presence in a soft watercolor bedtime storybook style.",
        "personality_traits": "playful, energetic, curious, bright, adventurous",
        "style_rules": "Soft watercolor/cartoon bedtime illustration, tiny star-like rounded form, sparkling magical glow, cheerful storybook feel.",
        "color_palette": "bright gold, soft yellow, pale white",
        "accessories": "none",
        "age_group": "3-7",
        "is_active": True,
    },
    {
        "name": "Whisperwing",
        "role": "guardian",
        "species": "winged spirit insect",
        "short_description": "A delicate silver-winged guide who quietly watches over stories.",
        "visual_description": "Delicate glowing insect with soft silver translucent wings, a graceful magical shimmer, and a calm wise presence in a soft watercolor bedtime storybook style.",
        "personality_traits": "wise, quiet, thoughtful, gentle, observant",
        "style_rules": "Soft watercolor/cartoon bedtime illustration, delicate rounded magical form, silver shimmer, calm bedtime elegance.",
        "color_palette": "silver, pale lavender, moonlight white",
        "accessories": "none",
        "age_group": "3-7",
        "is_active": True,
    },
]


def seed_characters(session: Session) -> None:
    """Insert canonical characters once without duplicating by name."""
    for payload in CANONICAL_CHARACTERS:
        statement = select(Character).where(Character.name == payload["name"])
        existing = session.exec(statement).first()
        if existing is None:
            session.add(Character(**payload))
    session.commit()
