"use client";

import type { MarketingPricingTier } from "@/lib/marketing-content";
import { MarketingCtaButton } from "@/components/marketing/MarketingCtaButton";

export function PricingCard({ tier }: { tier: MarketingPricingTier }) {
  const ctaLabel = tier.ctaKind === "upgrade" ? "Create Premium Account" : "Create Free Account";
  const ctaHref = tier.ctaKind === "upgrade" ? "/register/premium?source=pricing" : "/register/free?source=pricing";

  return (
    <div
      className={`rounded-3xl border p-6 shadow-sm ${
        tier.highlighted ? "border-indigo-200 bg-indigo-50/80" : "border-white/70 bg-white/85"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-2xl font-semibold text-slate-900">{tier.name}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">{tier.description}</p>
        </div>
        {tier.highlighted ? (
          <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-white">Popular</span>
        ) : null}
      </div>
      <p className="mt-5 text-4xl font-semibold tracking-tight text-slate-900">{tier.priceLabel}</p>
      <div className="mt-5 grid gap-2 text-sm text-slate-700">
        {tier.features.map((feature) => (
          <p key={feature} className="rounded-2xl bg-white/80 px-3 py-2">
            {feature}
          </p>
        ))}
      </div>
      <div className="mt-6">
        <MarketingCtaButton
          kind={tier.ctaKind}
          label={ctaLabel}
          source={`pricing_${tier.name.toLowerCase()}`}
          variant="secondary"
          className="w-full"
          href={ctaHref}
        />
      </div>
    </div>
  );
}
