"use client";

import Link from "next/link";

import type { FamilyDigestRead } from "@/lib/types";

interface FamilyDigestCardProps {
  digest: FamilyDigestRead;
  highlightText: string;
  tryNextText: string;
  storiesOpened: number;
  storiesCompleted: number;
  achievementsEarned: number;
  narrationUses: number;
  savedBooksAdded: number;
  completedStoryTitles: string[];
}

function formatDateRange(start: string, end: string) {
  const formatter = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
  return `${formatter.format(new Date(start))} - ${formatter.format(new Date(end))}`;
}

export function FamilyDigestCard({
  digest,
  highlightText,
  tryNextText,
  storiesOpened,
  storiesCompleted,
  achievementsEarned,
  narrationUses,
  savedBooksAdded,
  completedStoryTitles,
}: FamilyDigestCardProps) {
  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-indigo-700">Weekly family digest</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">{digest.title}</h2>
          <p className="mt-1 text-sm text-slate-500">{formatDateRange(digest.period_start, digest.period_end)}</p>
        </div>
        <Link
          href="/family-digest"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          View all digests
        </Link>
      </div>

      <div className="rounded-3xl bg-indigo-50 px-5 py-4 text-sm leading-6 text-indigo-950">{highlightText}</div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Stories opened</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{storiesOpened}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Stories completed</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{storiesCompleted}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Achievements earned</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{achievementsEarned}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Narration moments</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{narrationUses}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Saved this week</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{savedBooksAdded}</p>
        </div>
      </div>

      {completedStoryTitles.length ? (
        <div className="rounded-3xl bg-amber-50 px-5 py-4">
          <p className="text-sm font-medium text-slate-900">Completed stories</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{completedStoryTitles.join(", ")}</p>
        </div>
      ) : null}

      <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-4">
        <p className="text-sm font-medium text-slate-900">Try next</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">{tryNextText}</p>
      </div>
    </section>
  );
}
