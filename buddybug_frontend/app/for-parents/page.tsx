import type { Metadata } from "next";

import { CTASection } from "@/components/marketing/CTASection";

export const metadata: Metadata = {
  title: "Buddybug for Parents | Calmer Bedtime Routines and Safe Story Discovery",
  description: "Learn how Buddybug helps parents manage calmer bedtime reading, child profiles, safer discovery, and the difference between the Free Plan and Premium.",
  openGraph: {
    title: "Buddybug for Parents",
    description: "A calmer, safer family story experience with parental controls, child profiles, and bedtime-friendly discovery.",
  },
};

export default function ForParentsPage() {
  return (
    <div className="space-y-12 md:space-y-16">
      <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:p-10">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">For Parents</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">A story app built to make bedtime feel calmer, not noisier</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
          Buddybug is positioned around bedtime routines first. It helps parents find gentle stories faster, keep multiple children organized,
          and maintain safer defaults around age bands, autoplay, and premium content.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Calmer nights</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Bedtime mode, calm story discovery, and narrated reading options are designed to reduce friction at the end of the day.
          </p>
        </div>
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Safer story choices</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Age-aware recommendations and parental controls keep the catalog aligned with what you want each child to see.
          </p>
        </div>
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Multiple children, one account</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Switch between child profiles, keep preferences separate, and let Buddybug personalize by child rather than only by account.
          </p>
        </div>
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Free Plan or Premium</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            The Free Plan keeps things simple with 3 stories a week and 1 child profile. Premium is $9.99 and adds unlimited stories, bedtime packs, narration voices, saved library tools, unlimited child profiles, and personalised recommendations.
          </p>
        </div>
      </section>

      <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm">
        <h2 className="text-3xl font-semibold tracking-tight text-slate-900">Why this matters</h2>
        <p className="mt-4 text-base leading-7 text-slate-600">
          Parents do not need another noisy content app. Buddybug is meant to feel reassuring: gentle content, clear family controls,
          bedtime-first discovery, and room to grow into multilingual reading and older-child adventures later.
        </p>
      </section>

      <CTASection
        headline="Try Buddybug with your family tonight"
        description="Start with the Free Plan, then upgrade to Premium if the fuller bedtime routine fits your family."
        source="marketing_for_parents_footer"
      />
    </div>
  );
}
