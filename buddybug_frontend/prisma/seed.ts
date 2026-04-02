import { PrismaPg } from "@prisma/adapter-pg";
import { loadEnvConfig } from "@next/env";

import { StoryMode } from "../generated/prisma/client";
import { PrismaClient } from "../generated/prisma/client";
import { buildContentHtmlFromPages } from "../lib/prelaunch/story-content";
import type { PrelaunchStoryBook } from "../lib/prelaunch/story-content";

loadEnvConfig(process.cwd());

const prisma = new PrismaClient({
  adapter: new PrismaPg({
    connectionString:
      process.env.DATABASE_URL || process.env.DIRECT_URL || "postgresql://postgres:postgres@127.0.0.1:5432/buddybug",
  }),
});

const sampleStories: PrelaunchStoryBook[] = [
  {
    slug: "moonbeam-meadow-lullaby",
    title: "Moonbeam Meadow Lullaby",
    ageMin: 3,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "The Meadow Glow", text: "When the moon floated over the meadow, every daisy lifted a silver petal to say goodnight." },
      { pageNumber: 2, heading: "A Ribbon of Light", text: "Pip the bunny followed a ribbon of moonlight to a mossy hill where the breeze hummed the softest bedtime song." },
      { pageNumber: 3, heading: "Sleepy Wishes", text: "Pip tucked the song inside his heart, gave one quiet yawn, and let the stars watch over his dreams." },
    ],
  },
  {
    slug: "the-sleepy-cloud-post",
    title: "The Sleepy Cloud Post",
    ageMin: 3,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "Dream Deliveries", text: "Cloudlet drifted over the rooftops carrying peaceful dreams from window to window." },
      { pageNumber: 2, heading: "Starlight String", text: "Each dream was wrapped in a ribbon of starlight and smelled faintly of warm blankets and lavender." },
      { pageNumber: 3, heading: "A Quiet Town", text: "By the time Cloudlet reached the last chimney, the whole town was breathing in slow, cozy sighs." },
    ],
  },
  {
    slug: "boat-on-a-whisper-lake",
    title: "Boat on a Whisper Lake",
    ageMin: 4,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "Paper Boat", text: "Nora and her little paper boat floated across Whisper Lake, where the water spoke only in sleepy ripples." },
      { pageNumber: 2, heading: "Lantern Fireflies", text: "Friendly fireflies lit the reeds like lanterns and guided her toward a cove shaped like a crescent moon." },
      { pageNumber: 3, heading: "One Gentle Wish", text: "There, Nora whispered a wish for sweet dreams and rowed home before her eyelids grew too heavy to keep open." },
    ],
  },
  {
    slug: "the-lantern-tree",
    title: "The Lantern Tree",
    ageMin: 3,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "A Tree of Lanterns", text: "In the middle of a velvet garden stood a tree with lanterns instead of fruit." },
      { pageNumber: 2, heading: "Happy Thoughts", text: "Each lantern glowed when a child whispered one happy thought from the day just gone." },
      { pageNumber: 3, heading: "Garden Quiet", text: "When Mia shared hers, the whole tree shimmered softly and the garden tucked itself into silence." },
    ],
  },
  {
    slug: "owl-and-the-dream-map",
    title: "Owl and the Dream Map",
    ageMin: 5,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "The Silk Map", text: "Old Owl unfolded a dream map made of midnight blue silk and invited Theo to trace the calmest path in the sky." },
      { pageNumber: 2, heading: "Hills of Hush", text: "Together they crossed the Bay of Blankets and the Hills of Hush until the stars grew warm and near." },
      { pageNumber: 3, heading: "Moonlit Nest", text: "At last Theo curled into a moonlit nest high above the world, ready for a long, peaceful sleep." },
    ],
  },
  {
    slug: "the-tiny-train-to-drowsy-dell",
    title: "The Tiny Train to Drowsy Dell",
    ageMin: 3,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "Twilight Train", text: "A tiny train rolled through the twilight carrying pillows, pajamas, and one bell that only rang for bedtime." },
      { pageNumber: 2, heading: "Sleepy Passengers", text: "At every stop, drowsy animal passengers climbed aboard and shared their favorite quiet sounds." },
      { pageNumber: 3, heading: "Into Drowsy Dell", text: "By the last station, everyone was dozing gently as the train chuffed into Drowsy Dell." },
    ],
  },
  {
    slug: "star-pocket-night",
    title: "Star Pocket Night",
    ageMin: 4,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "A Secret Pocket", text: "Leela wore pajamas with a secret pocket that could hold one tiny star for safekeeping until morning." },
      { pageNumber: 2, heading: "The Shy Star", text: "She chose the faintest, shyest star in the sky and promised it a warm, quiet rest." },
      { pageNumber: 3, heading: "Heartbeat Light", text: "As soon as the star settled beside her heartbeat, Leela drifted into the gentlest dreams." },
    ],
  },
  {
    slug: "the-bear-who-collected-yawns",
    title: "The Bear Who Collected Yawns",
    ageMin: 3,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "Bramble's Satchel", text: "Bramble Bear walked through the forest with a satchel full of the sweetest yawns." },
      { pageNumber: 2, heading: "A Soft Yawn", text: "Whenever a squirrel or fox could not settle, Bramble shared one soft yawn and the whole woodland slowed down." },
      { pageNumber: 3, heading: "Forest Sleep", text: "At the end of the path, Bramble kept one last yawn for himself and slept until sunrise." },
    ],
  },
  {
    slug: "hush-harbor",
    title: "Hush Harbor",
    ageMin: 4,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "Whispering Waves", text: "Far beyond the busy day was a harbor where even the waves knew how to whisper." },
      { pageNumber: 2, heading: "Moon-Dock", text: "Sera tied her little sailboat to the moon-dock and listened to shells retell the calmest moments of the sea." },
      { pageNumber: 3, heading: "Foam Cradle", text: "When she was ready, the tide tucked her boat into a cradle of foam and rocked her toward sleep." },
    ],
  },
  {
    slug: "the-bedroom-garden-after-dark",
    title: "The Bedroom Garden After Dark",
    ageMin: 4,
    ageMax: 7,
    storyMode: StoryMode.BEDTIME,
    pages: [
      { pageNumber: 1, heading: "Moonflowers", text: "As soon as Sam switched off the lamp, tiny moonflowers quietly bloomed across the wallpaper beside the bed." },
      { pageNumber: 2, heading: "Silver Shadows", text: "They swayed in a silent breeze and painted silver shadows that felt like a lullaby." },
      { pageNumber: 3, heading: "Into Sleep", text: "Sam watched until the flowers folded their petals, then closed his eyes and followed them into sleep." },
    ],
  },
];

async function main() {
  for (const story of sampleStories) {
    await prisma.story.upsert({
      where: { slug: story.slug },
      update: {
        title: story.title,
        ageMin: story.ageMin,
        ageMax: story.ageMax,
        storyMode: story.storyMode,
        coverImageUrl: story.coverImageUrl || null,
        contentHtml: buildContentHtmlFromPages(story.title, story.pages),
        pagesJson: story.pages,
        isActive: true,
      },
      create: {
        slug: story.slug,
        title: story.title,
        ageMin: story.ageMin,
        ageMax: story.ageMax,
        storyMode: story.storyMode,
        coverImageUrl: story.coverImageUrl || null,
        contentHtml: buildContentHtmlFromPages(story.title, story.pages),
        pagesJson: story.pages,
        isActive: true,
      },
    });
  }

  console.log(`Seeded ${sampleStories.length} bedtime stories for the 3-7 pre-launch library.`);
}

main()
  .catch((error) => {
    console.error("Failed to seed bedtime stories", error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
