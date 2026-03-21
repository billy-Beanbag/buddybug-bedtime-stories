"use client";

import Link from "next/link";

import { trackRecommendationClicked } from "@/lib/analytics";
import { resolveApiUrl } from "@/lib/api";
import type { RecommendedBookScore, User } from "@/lib/types";

interface RecommendedBookCardProps {
  item: RecommendedBookScore;
  reasonPrefix?: string;
  analyticsSource?: string;
  token?: string | null;
  user?: User | null;
}

export function RecommendedBookCard({
  item,
  reasonPrefix,
  analyticsSource,
  token,
  user,
}: RecommendedBookCardProps) {
  const primaryReason = item.reasons[0] || `${item.language.toUpperCase()} story`;

  return (
    <Link
      href={`/reader/${item.book_id}`}
      onClick={() => {
        void trackRecommendationClicked(item.book_id, {
          token,
          user,
          language: item.language,
          source: analyticsSource || "recommended_book_card",
        });
      }}
      className="group relative block overflow-hidden rounded-3xl border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-4 shadow-[0_24px_60px_rgba(30,41,59,0.18)] transition hover:-translate-y-0.5 hover:shadow-[0_28px_70px_rgba(30,41,59,0.22)]"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
      <div className="relative flex gap-4">
        <div className="h-24 w-20 shrink-0 overflow-hidden rounded-2xl bg-slate-900/40 ring-1 ring-white/10">
          {item.cover_image_url ? (
            <img src={resolveApiUrl(item.cover_image_url)} alt={item.title} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center px-2 text-center text-xs text-indigo-100">No cover</div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-base font-semibold leading-tight text-white">{item.title}</h3>
            <span className="rounded-full border border-white/10 bg-white/10 px-2 py-1 text-xs font-medium text-indigo-100">
              {item.age_band}
            </span>
          </div>
          <p className="mt-2 text-sm text-indigo-100">
            {reasonPrefix ? `${reasonPrefix} ${primaryReason}` : primaryReason}
          </p>
          <p className="mt-3 text-xs uppercase tracking-wide text-indigo-200">{item.language.toUpperCase()}</p>
        </div>
      </div>
    </Link>
  );
}
