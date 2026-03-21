import Image from "next/image";

const reassuranceItems = [
  {
    title: "Age-appropriate by design",
    description: "Buddybug is shaped around bedtime-safe stories, gentle pacing, and child-friendly reading surfaces.",
  },
  {
    title: "Calm bedtime tone",
    description: "The experience avoids noisy rewards and pressure, keeping the focus on comfort and connection.",
  },
  {
    title: "Narration and offline-ready reading",
    description: "Families can read aloud themselves, use narration, and keep stories close for bedtime routines.",
  },
  {
    title: "Privacy and parental controls",
    description: "Parents stay in charge with child profiles, account-level controls, and family-first access patterns.",
  },
];

export function ParentReassurance() {
  return (
    <section className="rounded-[2.5rem] bg-[linear-gradient(180deg,#fffdf8,#ffffff)] p-6 shadow-[0_18px_45px_rgba(15,23,42,0.06)] ring-1 ring-amber-100/80 sm:p-8">
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <div>
          <div className="overflow-hidden rounded-[2rem] border border-amber-100 bg-amber-50 shadow-sm">
            <div className="relative aspect-[4/5]">
              <Image
                src="/home/verity-reading.jpeg"
                alt="A warm bedtime reading scene with Verity and the dachshunds"
                fill
                sizes="(max-width: 1024px) 100vw, 420px"
                className="object-cover object-center"
              />
            </div>
          </div>
          <p className="mt-5 text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">Parent reassurance</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            Built to feel trustworthy at the end of a long day
          </h2>
          <p className="mt-4 text-base leading-7 text-slate-600">
            Buddybug is designed for families who want bedtime to feel calmer, more consistent, and a little more
            magical without losing control.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {reassuranceItems.map((item) => (
            <article key={item.title} className="rounded-[1.75rem] border border-amber-100 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
