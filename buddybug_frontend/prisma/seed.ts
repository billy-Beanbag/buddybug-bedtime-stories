import { PrismaPg } from "@prisma/adapter-pg";
import { loadEnvConfig } from "@next/env";

import { PrismaClient } from "../generated/prisma/client";

loadEnvConfig(process.cwd());

const prisma = new PrismaClient({
  adapter: new PrismaPg({
    connectionString:
      process.env.DATABASE_URL || process.env.DIRECT_URL || "postgresql://postgres:postgres@127.0.0.1:5432/buddybug",
  }),
});

const sampleStories = [
  {
    slug: "moonbeam-meadow-lullaby",
    title: "Moonbeam Meadow Lullaby",
    ageMin: 3,
    ageMax: 5,
    contentHtml: `
      <h1>Moonbeam Meadow Lullaby</h1>
      <p>When the moon floated over the meadow, every daisy lifted a silver petal to say goodnight.</p>
      <p>A little bunny named Pip followed a ribbon of moonlight to a mossy hill, where the breeze hummed the softest bedtime song.</p>
      <p>Pip tucked the song inside his heart, yawned once, and fell asleep under the stars.</p>
    `,
  },
  {
    slug: "the-sleepy-cloud-post",
    title: "The Sleepy Cloud Post",
    ageMin: 3,
    ageMax: 6,
    contentHtml: `
      <h1>The Sleepy Cloud Post</h1>
      <p>Above the rooftops, Cloudlet the post-cloud drifted from window to window carrying peaceful dreams.</p>
      <p>Each dream was wrapped in starlight string and smelled faintly of warm blankets and lavender.</p>
      <p>By the time Cloudlet reached the final chimney, the whole town was breathing in slow, cozy sighs.</p>
    `,
  },
  {
    slug: "boat-on-a-whisper-lake",
    title: "Boat on a Whisper Lake",
    ageMin: 4,
    ageMax: 7,
    contentHtml: `
      <h1>Boat on a Whisper Lake</h1>
      <p>Nora and her paper boat floated across Whisper Lake, where the water spoke only in tiny sleepy ripples.</p>
      <p>Friendly fireflies lit the reeds like lanterns and guided the boat toward a cove shaped like a crescent moon.</p>
      <p>There, Nora made one gentle wish for sweet dreams and rowed home before her eyelids grew too heavy to keep open.</p>
    `,
  },
  {
    slug: "the-lantern-tree",
    title: "The Lantern Tree",
    ageMin: 3,
    ageMax: 7,
    contentHtml: `
      <h1>The Lantern Tree</h1>
      <p>In the middle of a velvet garden stood a tree with lanterns instead of fruit.</p>
      <p>Each lantern glowed when a child whispered one happy thought from the day just gone.</p>
      <p>When Mia whispered hers, the whole tree shimmered softly and the garden tucked itself into silence.</p>
    `,
  },
  {
    slug: "owl-and-the-dream-map",
    title: "Owl and the Dream Map",
    ageMin: 5,
    ageMax: 8,
    contentHtml: `
      <h1>Owl and the Dream Map</h1>
      <p>Old Owl unfolded a map made of midnight blue silk and invited Theo to trace a path to the calmest dream in the sky.</p>
      <p>Together they crossed the Bay of Blankets and the Hills of Hush until they found a moonlit nest high above the world.</p>
      <p>Theo curled up there with a grateful smile, ready for a long, peaceful sleep.</p>
    `,
  },
  {
    slug: "the-tiny-train-to-drowsy-dell",
    title: "The Tiny Train to Drowsy Dell",
    ageMin: 3,
    ageMax: 6,
    contentHtml: `
      <h1>The Tiny Train to Drowsy Dell</h1>
      <p>A tiny train rolled through the twilight carrying pillows, pajamas, and one golden bell that only rang for bedtime.</p>
      <p>At every stop, sleepy animal passengers climbed aboard and shared their favorite quiet sounds.</p>
      <p>By the last station, everyone was dozing gently as the train chuffed into Drowsy Dell.</p>
    `,
  },
  {
    slug: "star-pocket-night",
    title: "Star Pocket Night",
    ageMin: 4,
    ageMax: 7,
    contentHtml: `
      <h1>Star Pocket Night</h1>
      <p>Leela wore pajamas with a secret pocket that could hold one tiny star for safekeeping until morning.</p>
      <p>She chose the faintest, shyest star in the sky and promised it a warm, quiet rest.</p>
      <p>As soon as the star settled beside her heartbeat, Leela drifted into the gentlest dreams.</p>
    `,
  },
  {
    slug: "the-bear-who-collected-yawns",
    title: "The Bear Who Collected Yawns",
    ageMin: 3,
    ageMax: 5,
    contentHtml: `
      <h1>The Bear Who Collected Yawns</h1>
      <p>Bramble Bear walked through the forest with a satchel full of the sweetest yawns.</p>
      <p>Whenever a squirrel or fox could not settle, Bramble offered one soft yawn and the whole woodland slowed down.</p>
      <p>At the end of the path, Bramble kept one last yawn for himself and slept until sunrise.</p>
    `,
  },
  {
    slug: "hush-harbor",
    title: "Hush Harbor",
    ageMin: 5,
    ageMax: 8,
    contentHtml: `
      <h1>Hush Harbor</h1>
      <p>Far beyond the busy day was a harbor where even the waves knew how to whisper.</p>
      <p>Sera tied her little sailboat to the moon-dock and listened to shells retell the calmest moments of the sea.</p>
      <p>When she was ready, the tide tucked her boat into a cradle of foam and rocked her toward sleep.</p>
    `,
  },
  {
    slug: "the-bedroom-garden-after-dark",
    title: "The Bedroom Garden After Dark",
    ageMin: 4,
    ageMax: 7,
    contentHtml: `
      <h1>The Bedroom Garden After Dark</h1>
      <p>As soon as Sam switched off the lamp, tiny moonflowers quietly bloomed across the wallpaper beside the bed.</p>
      <p>They swayed in a silent breeze and painted silver shadows that felt like a lullaby.</p>
      <p>Sam watched until the flowers folded their petals, then closed his eyes and followed them into sleep.</p>
    `,
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
        contentHtml: story.contentHtml,
        isActive: true,
      },
      create: {
        ...story,
        isActive: true,
      },
    });
  }

  console.log(`Seeded ${sampleStories.length} calm bedtime stories.`);
}

main()
  .catch((error) => {
    console.error("Failed to seed bedtime stories", error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
