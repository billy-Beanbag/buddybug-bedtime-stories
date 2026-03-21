import type { ReactNode } from "react";

interface FeatureItem {
  title: string;
  description: string;
  icon: keyof typeof iconMap;
}

function IconShell({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-white/15 bg-white/10 text-white shadow-[0_14px_30px_rgba(15,23,42,0.18)] backdrop-blur">
      {children}
    </span>
  );
}

function BookIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M6 5.5A2.5 2.5 0 0 1 8.5 3H19v16H8.5A2.5 2.5 0 0 0 6 21.5v-16Z" />
      <path d="M6 5.5A2.5 2.5 0 0 0 3.5 8V19A2 2 0 0 0 5.5 21H6" />
    </svg>
  );
}

function AudioIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M5 14h3l4 4V6L8 10H5z" />
      <path d="M16 9a5 5 0 0 1 0 6" />
      <path d="M18.5 6.5a8.5 8.5 0 0 1 0 11" />
    </svg>
  );
}

function ChildIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5.5 20a6.5 6.5 0 0 1 13 0" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3l7 3v5c0 4.5-2.9 7.8-7 10-4.1-2.2-7-5.5-7-10V6l7-3Z" />
      <path d="m9.5 12 1.7 1.7 3.8-4" />
    </svg>
  );
}

function DigestIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="4" y="4" width="16" height="16" rx="3" />
      <path d="M8 9h8" />
      <path d="M8 13h8" />
      <path d="M8 17h5" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4 7 7 0 0 0 20 14.5Z" />
    </svg>
  );
}

const iconMap = {
  book: <BookIcon />,
  audio: <AudioIcon />,
  child: <ChildIcon />,
  shield: <ShieldIcon />,
  digest: <DigestIcon />,
  moon: <MoonIcon />,
};

const features: FeatureItem[] = [
  {
    icon: "book",
    title: "Illustrated Stories",
    description: "Soft, welcoming storybooks that feel made for quiet evening reading.",
  },
  {
    icon: "audio",
    title: "Narrated Bedtime Reading",
    description: "Read yourself or listen together when a calm voice is the gentlest choice.",
  },
  {
    icon: "child",
    title: "Child Profiles",
    description: "Keep each child's age, language, progress, and comfort preferences in one place.",
  },
  {
    icon: "shield",
    title: "Parental Controls",
    description: "Family-first controls help keep stories age-appropriate and bedtime-friendly.",
  },
  {
    icon: "digest",
    title: "Weekly Family Digests",
    description: "See a calm summary of family reading habits without turning bedtime into a scoreboard.",
  },
  {
    icon: "moon",
    title: "Bedtime Packs",
    description: "Move from one story to a thoughtful evening journey with a curated reading flow.",
  },
];

export function FeatureGrid() {
  return (
    <section className="space-y-6">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-indigo-700">Feature highlights</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          Everything a calm bedtime app needs, without the noise
        </h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {features.map((feature) => (
          <article
            key={feature.title}
            className="group relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.2)]"
          >
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
            <div className="pointer-events-none absolute -right-8 top-6 h-24 w-24 rounded-full bg-amber-100/10 blur-3xl transition duration-500 group-hover:scale-110" />
            <div className="relative">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-100">Buddybug feature</p>
            <IconShell>{iconMap[feature.icon]}</IconShell>
              <h3 className="mt-5 text-xl font-semibold text-white">{feature.title}</h3>
              <p className="mt-3 text-sm leading-6 text-indigo-100">{feature.description}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
