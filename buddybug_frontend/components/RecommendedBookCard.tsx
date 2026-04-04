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
      className="group relative block overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(145deg,#101936_0%,#162552_44%,#342d72_78%,#5d3793_100%)] p-5 shadow-[0_30px_80px_rgba(30,41,59,0.24)] transition hover:-translate-y-0.5 hover:shadow-[0_36px_90px_rgba(30,41,59,0.28)]"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.14),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.18),transparent_28%)]" />
      <div className="relative">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <span className="inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium tracking-[0.12em] text-indigo-100">
              Recommended tonight
            </span>
            <h3 className="mt-4 text-2xl font-semibold leading-tight text-white">{item.title}</h3>
            <p className="mt-3 max-w-xl text-sm text-indigo-100/90">
              {reasonPrefix ? `${reasonPrefix} ${primaryReason}` : primaryReason}
            </p>
          </div>
          <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-sm font-medium text-white/90">
            {item.age_band}
          </span>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <div className="h-40 w-28 shrink-0 overflow-hidden rounded-[1.6rem] border border-white/10 bg-slate-900/30 shadow-[0_18px_38px_rgba(8,15,38,0.35)]">
            {item.cover_image_url ? (
              <img src={resolveApiUrl(item.cover_image_url)} alt={item.title} className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full items-center justify-center bg-[linear-gradient(135deg,#1b2143_0%,#353d86_55%,#6a57eb_100%)] px-3 text-center text-xs text-indigo-50">
                No cover
              </div>
            )}
          </div>
          <div className="min-w-0 flex-1 rounded-[1.5rem] border border-white/10 bg-white/10 p-4">
            <p className="text-sm text-indigo-100/95">
              A calming Buddybug story chosen to make tonight&apos;s reading feel easy, gentle, and ready to start.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-white/90">
              <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1">Tonight's featured pick</span>
              <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1">{item.language.toUpperCase()}</span>
              <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1">Tap to open</span>
            </div>
          </div>
        </div>

        <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900">
          <span>Open story</span>
          <span aria-hidden="true">→</span>
        </div>
      </div>
    </Link>
  );
}
