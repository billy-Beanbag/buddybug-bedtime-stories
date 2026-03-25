import type { Metadata } from "next";

import { CTASection } from "@/components/marketing/CTASection";
import { howItWorksSteps } from "@/lib/marketing-content";

export const metadata: Metadata = {
  title: "How Buddybug Works | Family Story Time in 3 Steps",
  description: "Choose a child profile, read or listen to a story, and let Buddybug suggest the next one for bedtime.",
  openGraph: {
    title: "How Buddybug Works",
    description: "A simple 3-step story routine for calmer evenings, personalized reading, and a clear path from the Free Plan to Premium.",
  },
};

export default function HowItWorksPage() {
  return (
    <div className="space-y-12 md:space-y-16">
      <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:p-10">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">How It Works</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">A simple family flow designed for real bedtime use</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
          Buddybug keeps story time lightweight: choose who you are reading with, open a story, then let the app guide the next pick.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {howItWorksSteps.map((item) => (
          <div key={item.step} className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
            <p className="text-sm font-medium uppercase tracking-[0.16em] text-indigo-700">Step {item.step}</p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-900">{item.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{item.description}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Bedtime mode and age-aware filtering</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Buddybug can keep discovery focused on bedtime-safe stories and respect parental controls when a child profile is selected.
          </p>
        </div>
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Free Plan and Premium</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            The Free Plan is a lighter way to begin. Premium adds unlimited stories, full library access, bedtime packs, narration voices, saved library tools, unlimited child profiles, and personalised recommendations.
          </p>
        </div>
      </section>

      <CTASection
        headline="See Buddybug in action with free previews"
        description="Explore the Free Plan now, then unlock Premium when your family wants full access and the richer bedtime experience."
        source="marketing_how_it_works_footer"
      />
    </div>
  );
}
