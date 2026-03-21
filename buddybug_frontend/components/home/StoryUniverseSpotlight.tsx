import Image from "next/image";

const characters = [
  {
    name: "Verity",
    tone: "Warm mother figure",
    description: "A reassuring presence who helps bedtime feel softer, steadier, and lovingly guided.",
    image: "/home/verity-card.png",
    imageAlt: "Illustrated portrait of Verity reading at bedtime",
  },
  {
    name: "Dolly",
    tone: "Gentle dachshund dreamer",
    description: "Adds sweetness and comfort to the story world with a cozy, affectionate bedtime energy.",
    image: "/home/daphne-card.png",
    imageAlt: "Illustrated portrait of Dolly resting in a moonlit garden",
  },
  {
    name: "Daphne",
    tone: "Curious dachshund",
    description: "Brings playful wonder to quiet stories without ever tipping them out of bedtime calm.",
    image: "/home/dolly-card.png",
    imageAlt: "Illustrated portrait of Daphne in a moonlit garden",
  },
  {
    name: "Buddybug",
    tone: "Magical bedtime guide",
    description: "Leads families toward moonlit stories, glowing lanterns, and calmer ends to the day.",
    image: "/home/buddybug-card.png",
    imageAlt: "Illustrated portrait of Buddybug reading on a cloud",
  },
  {
    name: "Storylight Guardians",
    tone: "Protectors of the bedtime world",
    description: "A wider magical circle that helps the Buddybug universe feel special, safe, and full of wonder.",
    image: "/home/storylight-guardians-card.png",
    imageAlt: "Illustrated portrait of the Storylight Guardians gathered around bedtime light",
  },
];

export function StoryUniverseSpotlight() {
  return (
    <section className="space-y-6">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-indigo-700">Story universe spotlight</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          A warm world built for bedtime storytelling
        </h2>
        <p className="mt-3 text-base leading-7 text-slate-600">
          Buddybug isn't just a library. It's a gentle story universe filled with familiar guides, cozy companions,
          and magical bedtime light.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/82 shadow-[0_18px_45px_rgba(15,23,42,0.06)] md:col-span-2 xl:col-span-3">
          <div className="grid gap-0 lg:grid-cols-[0.82fr_1.18fr]">
            <div className="bg-[linear-gradient(135deg,#0b1c3f,#162d65)] p-4 sm:p-5">
              <div className="relative mx-auto max-w-md overflow-hidden rounded-[1.75rem] aspect-[4/5]">
                <Image
                  src="/home/verity-dogs-fairies.jpeg"
                  alt="Verity with Dolly and Daphne in a bedtime garden scene"
                  fill
                  sizes="(max-width: 1280px) 100vw, 520px"
                  className="object-cover object-center"
                />
              </div>
            </div>
            <div className="flex flex-col justify-center p-6 sm:p-8">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Inside Buddybug</p>
              <h3 className="mt-3 text-2xl font-semibold text-slate-900">A gentle cast of bedtime companions</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                The app can start to hint at its world through soft character scenes, warm story covers, and calm
                preview moments that make the library feel alive.
              </p>
            </div>
          </div>
        </article>

        {characters.map((character) => (
          <article
            key={character.name}
            className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/82 shadow-[0_18px_45px_rgba(15,23,42,0.06)]"
          >
            <div className="relative aspect-[16/10] overflow-hidden bg-[linear-gradient(135deg,#0b1c3f,#162d65)]">
              <Image
                src={character.image}
                alt={character.imageAlt}
                fill
                sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 360px"
                className="object-cover"
              />
            </div>
            <div className="p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">{character.tone}</p>
              <h3 className="mt-3 text-xl font-semibold text-slate-900">{character.name}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{character.description}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
