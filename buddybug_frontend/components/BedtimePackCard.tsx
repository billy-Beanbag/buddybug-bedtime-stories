"use client";

import type { BedtimePackRead, ChildProfileRead } from "@/lib/types";

interface BedtimePackCardProps {
  pack: BedtimePackRead;
  childProfiles?: ChildProfileRead[];
}

function formatDate(value: string | null) {
  if (!value) {
    return "Tonight";
  }
  return new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric" }).format(new Date(value));
}

export function BedtimePackCard({ pack, childProfiles = [] }: BedtimePackCardProps) {
  const childProfile = childProfiles.find((item) => item.id === pack.child_profile_id);

  return (
    <section className="relative space-y-4 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
      <div className="relative space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-indigo-100">Tonight's bedtime pack</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{pack.title}</h2>
          <p className="mt-1 text-sm text-indigo-200">{formatDate(pack.active_date)}</p>
        </div>
        <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-indigo-100">{pack.status}</span>
      </div>

      <p className="text-sm leading-6 text-indigo-100">
        {pack.description || "A calm multi-story wind-down for the evening."}
      </p>

      <div className="grid gap-3 sm:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-sm text-indigo-200">Scope</p>
          <p className="mt-1 font-medium text-white">{childProfile?.display_name || "Whole family"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-sm text-indigo-200">Language</p>
          <p className="mt-1 font-medium text-white">{pack.language?.toUpperCase() || "Flexible"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-sm text-indigo-200">Age band</p>
          <p className="mt-1 font-medium text-white">{pack.age_band || "Mixed ages"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-sm text-indigo-200">Narration</p>
          <p className="mt-1 font-medium text-white">{pack.prefer_narration ? "Preferred" : "Optional"}</p>
        </div>
      </div>

      {pack.generated_reason ? (
        <div className="rounded-3xl border border-white/10 bg-white/10 px-5 py-4 text-sm leading-6 text-indigo-50">
          {pack.generated_reason}
        </div>
      ) : null}
      </div>
    </section>
  );
}
