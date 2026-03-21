"use client";

import Link from "next/link";

import type { ChildProfileRead, ReadingPlanRead } from "@/lib/types";

interface ReadingPlanCardProps {
  plan: ReadingPlanRead;
  childProfiles: ChildProfileRead[];
}

function formatDays(targetDaysCsv: string | null) {
  if (!targetDaysCsv) {
    return "Spread gently across the week";
  }
  return targetDaysCsv
    .split(",")
    .filter(Boolean)
    .map((item) => item.trim().slice(0, 1).toUpperCase() + item.trim().slice(1))
    .join(", ");
}

export function ReadingPlanCard({ plan, childProfiles }: ReadingPlanCardProps) {
  const childProfile = childProfiles.find((item) => item.id === plan.child_profile_id);
  const scopeLabel = childProfile ? childProfile.display_name : "Whole family";

  return (
    <article className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-indigo-700">{plan.plan_type.replaceAll("_", " ")}</p>
          <h3 className="mt-2 text-xl font-semibold text-slate-900">{plan.title}</h3>
          <p className="mt-1 text-sm text-slate-600">{plan.description || "A gentle reading rhythm for calmer evenings."}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{plan.status}</span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Scope</p>
          <p className="mt-1 font-medium text-slate-900">{scopeLabel}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Sessions per week</p>
          <p className="mt-1 font-medium text-slate-900">{plan.sessions_per_week}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Language</p>
          <p className="mt-1 font-medium text-slate-900">{plan.preferred_language?.toUpperCase() || "Flexible"}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Narration</p>
          <p className="mt-1 font-medium text-slate-900">{plan.prefer_narration ? "Preferred" : "Optional"}</p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl bg-indigo-50 px-4 py-3 text-sm text-indigo-950">
        {formatDays(plan.target_days_csv)} • {plan.preferred_age_band || "Mixed ages"} •{" "}
        {plan.preferred_content_lane_key || "Flexible lane"}
      </div>

      <Link
        href={`/reading-plans/${plan.id}`}
        className="mt-4 inline-flex rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
      >
        Open plan
      </Link>
    </article>
  );
}
