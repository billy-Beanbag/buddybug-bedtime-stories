from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterVisualCanon:
    name: str
    role: str
    species: str
    appearance: str
    accessories: str
    scale_note: str
    must_not_show: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocationVisualCanon:
    key: str
    label: str
    visual_description: str
    lighting: str
    recurring_props: tuple[str, ...] = ()


CHARACTER_VISUAL_CANON: dict[str, CharacterVisualCanon] = {
    "Verity": CharacterVisualCanon(
        name="Verity",
        role="warm mother figure",
        species="human",
        appearance=(
            "young woman with long golden-blonde hair, warm brown eyes, a gentle smile, "
            "and a simple light cream or white dress in a soft storybook style"
        ),
        accessories="usually no jewelry or extra accessories",
        scale_note="adult human, larger than the dachshunds and seated or kneeling calmly near them",
        must_not_show=("do not make her a child", "do not change her hair to dark colours"),
    ),
    "Dolly": CharacterVisualCanon(
        name="Dolly",
        role="gentle companion",
        species="grey dachshund",
        appearance=(
            "small smooth-coated grey dachshund with soft expressive eyes, gentle face, "
            "and a calm, thoughtful body posture"
        ),
        accessories="blue collar",
        scale_note="small dachshund, usually close to Verity and slightly lighter than Daphne",
        must_not_show=(
            "do not describe or depict Dolly as a rabbit",
            "do not describe or depict Dolly as a bear",
            "do not change the blue collar",
        ),
    ),
    "Daphne": CharacterVisualCanon(
        name="Daphne",
        role="playful companion",
        species="black-and-tan dachshund",
        appearance=(
            "small black-and-tan dachshund with tan eyebrows, tan muzzle, bright curious eyes, "
            "and a more playful alert posture than Dolly"
        ),
        accessories="red collar with a gold star tag",
        scale_note="small dachshund, similar size to Dolly but with darker coat and more energetic pose",
        must_not_show=(
            "do not describe or depict Daphne as a bear",
            "do not describe or depict Daphne as a rabbit",
            "do not remove the red collar and gold star tag",
        ),
    ),
    "Buddybug": CharacterVisualCanon(
        name="Buddybug",
        role="story keeper",
        species="golden firefly guardian",
        appearance=(
            "small glowing golden firefly with a rounded friendly face, bright warm eyes, "
            "and tiny luminous wings"
        ),
        accessories="no clothing or handheld items",
        scale_note="tiny flying guardian, clearly smaller than the dogs and used as a warm point of light",
        must_not_show=(
            "do not depict Buddybug as a ladybird",
            "do not depict Buddybug as a ladybug",
            "do not depict Buddybug as a beetle",
            "do not remove Buddybug's tiny luminous wings",
        ),
    ),
    "Glowmoth": CharacterVisualCanon(
        name="Glowmoth",
        role="Storylight Guardian",
        species="soft blue moth guardian",
        appearance=(
            "pale blue and silver moth with broad velvet wings, gentle sleepy eyes, "
            "and a soothing calm glow"
        ),
        accessories="no clothing or objects",
        scale_note="small floating guardian, usually a little larger in wing span than Buddybug",
    ),
    "Twinklet": CharacterVisualCanon(
        name="Twinklet",
        role="Storylight Guardian",
        species="star-shaped glow bug",
        appearance=(
            "tiny bright yellow star-shaped guardian with a smiling face, soft points, "
            "and a playful magical sparkle"
        ),
        accessories="no clothing or objects",
        scale_note="very small floating guardian, compact and bright like a cheerful little star",
    ),
    "Whisperwing": CharacterVisualCanon(
        name="Whisperwing",
        role="Storylight Guardian",
        species="silvery winged dream guide",
        appearance=(
            "soft silver-white guardian with delicate translucent wings, calm round eyes, "
            "and a quiet moonlit shimmer"
        ),
        accessories="no clothing or objects",
        scale_note="small floating guardian with the most delicate, pale colouring of the three guardians",
    ),
}


LOCATION_VISUAL_CANON: dict[str, LocationVisualCanon] = {
    "cozy bedroom": LocationVisualCanon(
        key="cozy bedroom",
        label="Verity's bedroom",
        visual_description="a warm bedtime room with bed, pillows, patchwork blanket, rocking chair, books, and soft storybook details",
        lighting="soft amber bedside glow with gentle moonlight through the window",
        recurring_props=("patchwork blanket", "pillows", "rocking chair", "books"),
    ),
    "verity's bedroom": LocationVisualCanon(
        key="verity's bedroom",
        label="Verity's bedroom",
        visual_description="a warm bedtime room with bed, pillows, patchwork blanket, rocking chair, books, and soft storybook details",
        lighting="soft amber bedside glow with gentle moonlight through the window",
        recurring_props=("patchwork blanket", "pillows", "rocking chair", "books"),
    ),
    "inside the house": LocationVisualCanon(
        key="inside the house",
        label="Verity's house",
        visual_description="a cozy storybook home interior with warm wood, rugs, shelves, and bedtime calm",
        lighting="warm indoor lantern or lamp light",
        recurring_props=("rugs", "shelves", "storybooks", "warm wooden details"),
    ),
    "breakfast kitchen": LocationVisualCanon(
        key="breakfast kitchen",
        label="Verity's kitchen",
        visual_description="a welcoming family kitchen with wooden table, mixing bowl, berries, flour, and homely baking details",
        lighting="warm morning or afternoon house light",
        recurring_props=("mixing bowl", "wooden spoon", "blueberries", "flour dust"),
    ),
    "family kitchen": LocationVisualCanon(
        key="family kitchen",
        label="Verity's kitchen",
        visual_description="a welcoming family kitchen with wooden table, mixing bowl, berries, flour, and homely baking details",
        lighting="warm morning or afternoon house light",
        recurring_props=("mixing bowl", "wooden spoon", "blueberries", "flour dust"),
    ),
    "family living room": LocationVisualCanon(
        key="family living room",
        label="Verity's living room",
        visual_description="a cozy family living room with sofa, rug, chairs, coffee table, and clear homemade fort-building details",
        lighting="warm indoor evening family-room light with soft cozy clarity",
        recurring_props=("sofa", "blanket fort", "cushions", "rug"),
    ),
    "zoo picnic lawn": LocationVisualCanon(
        key="zoo picnic lawn",
        label="Zoo picnic lawn",
        visual_description="an open picnic lawn at the zoo with basket, checked cloth, railings or enclosure cues, and clear daytime family outing details",
        lighting="soft daytime outdoor light with natural grass and open-air clarity",
        recurring_props=("picnic basket", "checked cloth", "open grass", "zoo rail"),
    ),
    "garden path": LocationVisualCanon(
        key="garden path",
        label="Moonlit garden path",
        visual_description="a winding path through flowers, grass, and storybook greenery near Verity's home",
        lighting="gentle dusky garden light with warm glowing path accents",
        recurring_props=("flowers", "stones", "glowing path", "garden leaves"),
    ),
    "moonlit garden": LocationVisualCanon(
        key="moonlit garden",
        label="Moonlit Garden",
        visual_description="a dreamy but clear story garden with flowers, glowing paths, soft shrubs, and gentle magic",
        lighting="moonlit blue night with warm path glows and lantern accents",
        recurring_props=("flowers", "glowing path", "lanterns", "petals"),
    ),
    "storybook clearing": LocationVisualCanon(
        key="storybook clearing",
        label="Storybook Clearing",
        visual_description="an open clearing with books, lanterns, soft grass, and a welcoming storybook glade feeling",
        lighting="warm lantern glow in a calm twilight setting",
        recurring_props=("open books", "lanterns", "grass", "flower beds"),
    ),
    "reading nook": LocationVisualCanon(
        key="reading nook",
        label="reading nook",
        visual_description="a cozy indoor reading space with stacked books, cushions, a soft rug, and a low shelf",
        lighting="warm indoor reading light",
        recurring_props=("stacked books", "cushions", "soft rug", "book basket"),
    ),
    "library reading nook": LocationVisualCanon(
        key="library reading nook",
        label="Library reading nook",
        visual_description="a cozy library corner with stacked books, cushions, a soft rug, low shelves, and a calm indoor story-time feeling",
        lighting="warm indoor reading light",
        recurring_props=("stacked books", "cushions", "soft rug", "book basket"),
    ),
    "dream pond": LocationVisualCanon(
        key="dream pond",
        label="Dream Pond",
        visual_description="a peaceful pond with lilies, swans or birds, curved bridge, and soft glowing paths nearby",
        lighting="gentle moonlight reflected on still water",
        recurring_props=("lilies", "bridge", "pond water", "glowing reflections"),
    ),
    "guardian glade": LocationVisualCanon(
        key="guardian glade",
        label="Guardian Glade",
        visual_description="a tucked-away glowing glade with tiny guardian dwellings, mushrooms, and soft magic",
        lighting="warm hidden lantern light with magical sparkle",
        recurring_props=("mushrooms", "tiny doors", "lanterns", "glowing greenery"),
    ),
    "story tree": LocationVisualCanon(
        key="story tree",
        label="Story Tree",
        visual_description="an old magical tree with roots, books, and lanterns gathered around it like a storytelling place",
        lighting="warm magical tree-light mixed with evening sky",
        recurring_props=("tree roots", "open books", "lanterns", "soft flowers"),
    ),
    "dolly & daphne's basket bed": LocationVisualCanon(
        key="dolly & daphne's basket bed",
        label="Dolly & Daphne's basket bed",
        visual_description="a cozy basket bed area with blankets, cushions, and familiar dog-bed details near Verity",
        lighting="warm bedside or hearth light",
        recurring_props=("basket bed", "blankets", "cushions"),
    ),
}


def normalize_location_key(location: str | None) -> str:
    return (location or "").strip().casefold()


def get_character_visual_canon(name: str) -> CharacterVisualCanon | None:
    return CHARACTER_VISUAL_CANON.get(name)


def get_location_visual_canon(location: str | None) -> LocationVisualCanon | None:
    normalized = normalize_location_key(location)
    if normalized in LOCATION_VISUAL_CANON:
        return LOCATION_VISUAL_CANON[normalized]
    return None


def build_character_visual_lines(characters: list[str]) -> list[str]:
    lines: list[str] = []
    for name in characters:
        canon = get_character_visual_canon(name)
        if canon is None:
            continue
        lines.extend(
            [
                f"{canon.name}: {canon.role}, {canon.species}.",
                f"{canon.name} appearance: {canon.appearance}.",
                f"{canon.name} accessories: {canon.accessories}.",
                f"{canon.name} scale: {canon.scale_note}.",
            ]
        )
        lines.extend(canon.must_not_show)
    return lines


def build_location_visual_lines(location: str | None) -> list[str]:
    canon = get_location_visual_canon(location)
    if canon is None:
        return []
    props = ", ".join(canon.recurring_props) if canon.recurring_props else "story-appropriate props"
    return [
        f"Location: {canon.label}.",
        f"Location look: {canon.visual_description}.",
        f"Lighting: {canon.lighting}.",
        f"Recurring props to use when relevant: {props}.",
    ]
