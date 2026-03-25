"use client";

import { useEffect, useRef, useState } from "react";

import { CTASection } from "@/components/marketing/CTASection";
import { MarketingPageTracker } from "@/components/marketing/MarketingPageTracker";
import { PricingCard } from "@/components/marketing/PricingCard";
import { useAuth } from "@/context/AuthContext";
import {
  trackMessageVariantClicked,
  trackMessageVariantExposed,
  trackPricingCtaClicked,
} from "@/lib/analytics";
import { pricingTiers } from "@/lib/marketing-content";
import { DEFAULT_MESSAGE_EXPERIMENT_BUNDLE, fetchMessageExperimentBundle } from "@/lib/message-experiments";
import type { MessageExperimentSurfaceCopy } from "@/lib/types";

const DEFAULT_PRICING_COPY = DEFAULT_MESSAGE_EXPERIMENT_BUNDLE.pricing_page;

export function PricingPageContent() {
  const { token, user } = useAuth();
  const [copy, setCopy] = useState<MessageExperimentSurfaceCopy>(DEFAULT_PRICING_COPY);
  const [copyLoaded, setCopyLoaded] = useState(false);
  const exposureTracked = useRef(false);
  const startFreeTarget = "/register/free?source=pricing";
  const upgradeTarget = "/register/premium?source=pricing";

  useEffect(() => {
    let cancelled = false;

    void fetchMessageExperimentBundle({ token, user }).then((bundle) => {
      if (cancelled) {
        return;
      }
      setCopy(bundle.pricing_page || DEFAULT_PRICING_COPY);
      setCopyLoaded(true);
    });

    return () => {
      cancelled = true;
    };
  }, [token, user]);

  useEffect(() => {
    if (!copyLoaded || exposureTracked.current) {
      return;
    }
    exposureTracked.current = true;
    void trackMessageVariantExposed("pricing_page", {
      token,
      user,
      experimentKey: copy.experiment_key,
      experimentVariant: copy.variant,
      source: "pricing_page",
    });
  }, [copy, token, user]);

  function trackPricingAction(target: string) {
    void trackMessageVariantClicked("pricing_page", {
      token,
      user,
      experimentKey: copy?.experiment_key,
      experimentVariant: copy?.variant,
      source: "pricing_page",
      target,
    });
    void trackPricingCtaClicked({
      token,
      user,
      experimentKey: copy?.experiment_key,
      experimentVariant: copy?.variant,
      source: "pricing_page",
      target,
    });
  }

  return (
    <div className="space-y-12 md:space-y-16">
      <MarketingPageTracker eventName="marketing_pricing_viewed" source="marketing_pricing" />
      <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:p-10">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">Pricing</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">{copy.headline}</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">{copy.description}</p>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        {pricingTiers.map((tier) => (
          <PricingCard key={tier.name} tier={tier} />
        ))}
      </section>

      <section className="rounded-3xl border border-white/70 bg-white/80 p-6 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">What Premium unlocks</h2>
        <p className="mt-3 text-base leading-7 text-slate-600">
          Premium is designed for families who want Buddybug to become part of a real routine: unlimited stories, full
          library access, bedtime packs, narration voices, saved library tools, unlimited child profiles, and more
          personalised recommendations.
        </p>
      </section>

      <CTASection
        headline={copy.cta_headline || "Pick a plan and create your Buddybug account"}
        description={
          copy.cta_description ||
          "Both options create the same Buddybug account record. Free takes you into guided setup, while Premium adds checkout before the same getting-started flow."
        }
        source="marketing_pricing_footer"
        startFreeLabel={copy.primary_cta_label || "Create Free Account"}
        upgradeLabel={copy.secondary_cta_label || "Create Premium Account"}
        onStartFreeClick={() => trackPricingAction(startFreeTarget)}
        onUpgradeClick={() => trackPricingAction(upgradeTarget)}
        startFreeHref={startFreeTarget}
        upgradeHref={upgradeTarget}
        showExploreButton={false}
        startFreeVariant="secondary"
        upgradeVariant="secondary"
      />
    </div>
  );
}
