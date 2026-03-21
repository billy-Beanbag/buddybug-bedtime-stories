"use client";

import Link from "next/link";

import type { DiscoverySearchResult } from "@/lib/types";

interface ReadingPlanSuggestionsProps {
  suggestions: DiscoverySearchResult[];
}

export function ReadingPlanSuggestions({ suggestions }: ReadingPlanSuggestionsProps) {
  if (!suggestions.length) {
    return (
      <div className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4 text-sm text-slate-600">
        No matching story suggestions are ready yet for this plan.
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {suggestions.map((item) => (
        <Link
          key={item.book_id}
          href={`/reader/${item.book_id}`}
          className="rounded-[2rem] border border-white/70 bg-white/85 p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-1 text-sm text-slate-600">
                {item.age_band} • {item.language.toUpperCase()} • {item.content_lane_key || "Flexible lane"}
              </p>
            </div>
            <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">Open</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-700">
            {item.reasons?.[0] || "A gentle match for this reading plan."}
          </p>
        </Link>
      ))}
    </div>
  );
}
