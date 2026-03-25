import type { Metadata } from "next";

import { CTASection } from "@/components/marketing/CTASection";
import { FeatureGrid } from "@/components/marketing/FeatureGrid";
import { MarketingPageTracker } from "@/components/marketing/MarketingPageTracker";
import { featureCards } from "@/lib/marketing-content";

export const metadata: Metadata = {
  title: "Buddybug Features | Narrated Stories, Child Profiles, and Bedtime Tools",
  description: "Explore illustrated stories, narrated playback, child profiles, parental controls, saved-library tools, and more.",
  openGraph: {
    title: "Buddybug Features",
    description: "Illustrated bedtime stories, narrated playback, family profiles, and safer discovery tools in one app.",
  },
};

export default function FeaturesPage() {
  return (
    <div className="space-y-12 md:space-y-16">
      <MarketingPageTracker eventName="marketing_features_viewed" source="marketing_features" />
      <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:p-10">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">Features</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">Everything Buddybug already does for families</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
          Buddybug is designed around calm bedtime routines today, with the foundations to grow into deeper family reading,
          older-child adventures, and multilingual family use over time.
        </p>
      </section>

      <FeatureGrid
        title="Core family story features"
        description="Each feature is designed to feel useful on day one and extensible as the catalog grows."
        items={featureCards}
      />

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Bedtime-first experience</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Calm stories, bedtime mode, and gentle discovery are positioned for 3-7 year-olds and real evening routines.
          </p>
        </div>
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Premium-ready value</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Narration, saved library tools, premium voices, and family personalization give subscribers a clear reason to upgrade.
          </p>
        </div>
        <div className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Built to expand</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            The platform already supports editorial publishing, discovery metadata, multilingual foundations, and 8-12 growth paths.
          </p>
        </div>
      </section>

      <CTASection
        headline="See how Buddybug fits your bedtime routine"
        description="Start with free previews, then unlock the full story experience when your family is ready."
        source="marketing_features_footer"
      />
    </div>
  );
}
