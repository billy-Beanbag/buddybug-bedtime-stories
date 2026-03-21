"use client";

import Link from "next/link";

import type { SeasonalCampaignRead } from "@/lib/types";

export function CampaignCarousel({ campaigns }: { campaigns: SeasonalCampaignRead[] }) {
  if (!campaigns.length) {
    return null;
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-1">
      {campaigns.map((campaign) => (
        <Link
          key={campaign.id}
          href={`/campaigns/${campaign.key}`}
          className="min-w-[240px] rounded-3xl border border-white/70 bg-white/85 p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
        >
          <p className="text-sm font-semibold text-slate-900">{campaign.title}</p>
          <p className="mt-2 text-sm text-slate-600">
            {campaign.description || "A themed collection of family-friendly seasonal stories."}
          </p>
          <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">
            {campaign.language?.toUpperCase() || "All languages"} {campaign.age_band ? `• ${campaign.age_band}` : ""}
          </p>
        </Link>
      ))}
    </div>
  );
}
