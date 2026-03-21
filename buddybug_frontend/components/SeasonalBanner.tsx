"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import { apiGet } from "@/lib/api";
import type { SeasonalCampaignRead } from "@/lib/types";

interface SeasonalBannerProps {
  campaign?: SeasonalCampaignRead | null;
  surface?: "home" | "discover" | "campaign";
}

const BANNER_STYLES: Record<string, string> = {
  spring_glow: "from-emerald-200 via-lime-100 to-sky-100 text-emerald-950",
  cozy_night: "from-indigo-900 via-slate-900 to-sky-900 text-white",
};

export function SeasonalBanner({ campaign, surface = "home" }: SeasonalBannerProps) {
  const { token, isAuthenticated } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const { locale } = useLocale();
  const [resolvedCampaign, setResolvedCampaign] = useState<SeasonalCampaignRead | null>(campaign || null);

  useEffect(() => {
    if (campaign) {
      setResolvedCampaign(campaign);
      return;
    }

    async function loadCampaign() {
      try {
        const items = await apiGet<SeasonalCampaignRead[]>("/campaigns/active", {
          token,
          query: {
            language: selectedChildProfile?.language || locale,
            age_band: selectedChildProfile?.age_band,
            content_lane_key: selectedChildProfile?.content_lane_key,
            child_profile_id: isAuthenticated ? selectedChildProfile?.id : undefined,
          },
        });
        setResolvedCampaign(items[0] || null);
      } catch {
        setResolvedCampaign(null);
      }
    }

    void loadCampaign();
  }, [
    campaign,
    isAuthenticated,
    locale,
    selectedChildProfile?.age_band,
    selectedChildProfile?.content_lane_key,
    selectedChildProfile?.id,
    selectedChildProfile?.language,
    token,
  ]);

  if (!resolvedCampaign) {
    return null;
  }

  const styleClass =
    BANNER_STYLES[resolvedCampaign.banner_style_key || ""] ||
    "from-amber-100 via-rose-50 to-indigo-50 text-slate-900";
  const ctaHref = resolvedCampaign.homepage_cta_route || `/campaigns/${resolvedCampaign.key}`;
  const ctaLabel = resolvedCampaign.homepage_cta_label || "Explore this theme";

  return (
    <section
      className={`rounded-[2.25rem] bg-gradient-to-br p-6 shadow-sm md:p-8 ${styleClass}`}
      data-surface={surface}
    >
      <p className="text-sm font-medium uppercase tracking-[0.18em] opacity-90">
        {resolvedCampaign.homepage_badge_text || "Seasonal campaign"}
      </p>
      <h2 className="mt-3 text-3xl font-semibold tracking-tight">{resolvedCampaign.title}</h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 opacity-90">
        {resolvedCampaign.description || "Fresh themed story picks are ready for this moment in the Buddybug calendar."}
      </p>
      <div className="mt-5 flex flex-wrap gap-3 text-xs uppercase tracking-wide opacity-80">
        <span>{resolvedCampaign.language?.toUpperCase() || "All languages"}</span>
        <span>{resolvedCampaign.age_band || "All ages"}</span>
        {resolvedCampaign.content_lane_key ? <span>{resolvedCampaign.content_lane_key}</span> : null}
      </div>
      <Link
        href={ctaHref}
        className="mt-6 inline-flex rounded-2xl bg-white/90 px-4 py-3 text-sm font-medium text-slate-900"
      >
        {ctaLabel}
      </Link>
    </section>
  );
}
