"use client";

import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { heroBullets } from "@/lib/marketing-content";
import { MarketingCtaButton } from "@/components/marketing/MarketingCtaButton";
import { fetchMessageExperimentBundle } from "@/lib/message-experiments";
import { trackMessageVariantClicked, trackMessageVariantExposed } from "@/lib/analytics";
import type { MessageExperimentSurfaceCopy } from "@/lib/types";

export function HeroSection({ surface = "homepage_hero" }: { surface?: string }) {
  const { isAuthenticated, token, user } = useAuth();
  const [copy, setCopy] = useState<MessageExperimentSurfaceCopy | null>(null);
  const exposureTracked = useRef(false);

  useEffect(() => {
    void fetchMessageExperimentBundle({ token, user }).then((bundle) => setCopy(bundle.homepage_cta));
  }, [token, user]);

  useEffect(() => {
    if (!copy || exposureTracked.current) {
      return;
    }
    exposureTracked.current = true;
    void trackMessageVariantExposed(surface, {
      token,
      user,
      experimentKey: copy.experiment_key,
      experimentVariant: copy.variant,
      source: surface,
    });
  }, [copy, surface, token, user]);

  return (
    <section className="grid gap-8 rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:grid-cols-[1.2fr_0.8fr] md:p-10">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-indigo-700">
          {copy?.eyebrow || "Buddybug Storylight"}
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
          {copy?.headline || "Beautiful bedtime stories for children, powered by imagination."}
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
          {copy?.description ||
            "Illustrated, narrated, calming stories that grow with your family, from cozy bedtime reading to personalized daily story picks."}
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <MarketingCtaButton
            kind="start-free"
            label={isAuthenticated ? "Open App" : copy?.primary_cta_label || "Start Free"}
            source="hero_primary"
            onClick={() => {
              void trackMessageVariantClicked(surface, {
                token,
                user,
                experimentKey: copy?.experiment_key,
                experimentVariant: copy?.variant,
                source: surface,
                target: isAuthenticated ? "/library" : "/register",
              });
            }}
          />
          <MarketingCtaButton
            kind="explore"
            label={copy?.secondary_cta_label || "Explore Stories"}
            source="hero_secondary"
            variant="secondary"
          />
          <MarketingCtaButton
            kind="pricing"
            label={copy?.pricing_cta_label || "View Pricing"}
            source="hero_pricing"
            variant="secondary"
          />
        </div>
      </div>
      <div className="rounded-[2rem] bg-gradient-to-br from-indigo-50 via-sky-50 to-amber-50 p-6">
        <p className="text-sm font-medium text-slate-700">Built for calm family story time</p>
        <div className="mt-4 space-y-3">
          {heroBullets.map((item) => (
            <div key={item} className="rounded-2xl bg-white/90 px-4 py-3 text-sm text-slate-700 shadow-sm">
              {item}
            </div>
          ))}
        </div>
        <div className="mt-6 rounded-3xl border border-indigo-100 bg-white/90 p-5 shadow-sm">
          <p className="text-sm font-semibold text-slate-900">What families get</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Child profiles, bedtime-safe discovery, narrated stories, saved favorites, and a simple path from free
            preview to premium family access.
          </p>
        </div>
      </div>
    </section>
  );
}
