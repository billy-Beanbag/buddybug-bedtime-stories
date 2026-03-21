"use client";

import { MarketingCtaButton } from "@/components/marketing/MarketingCtaButton";

export function CTASection({
  headline,
  description,
  source,
  startFreeLabel = "Start Free",
  upgradeLabel = "Upgrade to Premium",
  exploreLabel = "Explore Stories",
  onStartFreeClick,
  onUpgradeClick,
  startFreeHref,
  upgradeHref,
  showExploreButton = true,
  startFreeVariant = "primary",
  upgradeVariant = "secondary",
}: {
  headline: string;
  description: string;
  source: string;
  startFreeLabel?: string;
  upgradeLabel?: string;
  exploreLabel?: string;
  onStartFreeClick?: () => void;
  onUpgradeClick?: () => void;
  startFreeHref?: string;
  upgradeHref?: string;
  showExploreButton?: boolean;
  startFreeVariant?: "primary" | "secondary" | "ghost";
  upgradeVariant?: "primary" | "secondary" | "ghost";
}) {
  return (
    <section className="rounded-[2.5rem] border border-indigo-100 bg-gradient-to-br from-white via-indigo-50/70 to-sky-50/80 p-8 shadow-sm md:p-10">
      <div className="max-w-3xl">
        <h2 className="text-3xl font-semibold tracking-tight text-slate-900">{headline}</h2>
        <p className="mt-3 text-base leading-7 text-slate-600">{description}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <MarketingCtaButton
            kind="start-free"
            label={startFreeLabel}
            source={`${source}_start_free`}
            onClick={onStartFreeClick}
            href={startFreeHref}
            variant={startFreeVariant}
          />
          <MarketingCtaButton
            kind="upgrade"
            label={upgradeLabel}
            source={`${source}_upgrade`}
            variant={upgradeVariant}
            onClick={onUpgradeClick}
            href={upgradeHref}
          />
          {showExploreButton ? (
            <MarketingCtaButton kind="explore" label={exploreLabel} source={`${source}_explore`} variant="secondary" />
          ) : null}
        </div>
      </div>
    </section>
  );
}
