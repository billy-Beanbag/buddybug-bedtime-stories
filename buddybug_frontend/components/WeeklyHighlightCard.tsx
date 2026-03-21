"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type { FamilyDigestSummaryCardResponse } from "@/lib/types";

interface WeeklyHighlightCardProps {
  summary?: FamilyDigestSummaryCardResponse | null;
  loadLatest?: boolean;
  compact?: boolean;
}

function formatDateRange(start: string, end: string) {
  const formatter = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
  return `${formatter.format(new Date(start))} - ${formatter.format(new Date(end))}`;
}

export function WeeklyHighlightCard({ summary: providedSummary = null, loadLatest = false, compact = false }: WeeklyHighlightCardProps) {
  const { token, isAuthenticated, isLoading } = useAuth();
  const [summary, setSummary] = useState<FamilyDigestSummaryCardResponse | null>(providedSummary);

  useEffect(() => {
    setSummary(providedSummary);
  }, [providedSummary]);

  useEffect(() => {
    if (!loadLatest || providedSummary || isLoading || !isAuthenticated || !token) {
      return;
    }

    void apiGet<FamilyDigestSummaryCardResponse>("/family-digest/me/summary-card", { token })
      .then((response) => setSummary(response))
      .catch(() => setSummary(null));
  }, [isAuthenticated, isLoading, loadLatest, providedSummary, token]);

  if (!summary) {
    return null;
  }

  return (
    <section
      className={`relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)] ${
        compact ? "p-5" : "p-6"
      }`}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
      <div className="relative">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-indigo-100">This week</p>
          <h2 className={`${compact ? "mt-2 text-xl" : "mt-2 text-2xl"} font-semibold text-white`}>{summary.title}</h2>
          <p className="mt-1 text-sm text-indigo-200">{formatDateRange(summary.period_start, summary.period_end)}</p>
        </div>
        <Link
          href="/family-digest"
          className="rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white"
        >
          Open family digest
        </Link>
      </div>

      <p className="mt-4 text-sm leading-6 text-indigo-100">{summary.highlight_text}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-sm text-indigo-200">Stories completed</p>
          <p className="mt-1 text-2xl font-semibold text-white">{summary.stories_completed}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-sm text-indigo-200">Achievements earned</p>
          <p className="mt-1 text-2xl font-semibold text-white">{summary.achievements_earned}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-sm text-indigo-200">Child snapshots</p>
          <p className="mt-1 text-2xl font-semibold text-white">{summary.child_count}</p>
        </div>
      </div>
      </div>
    </section>
  );
}
