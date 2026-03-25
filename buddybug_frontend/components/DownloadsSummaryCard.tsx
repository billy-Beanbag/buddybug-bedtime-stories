"use client";

import Link from "next/link";

import { AppSectionCard } from "@/components/AppSectionCard";

interface DownloadsSummaryCardProps {
  savedCount: number;
}

export function DownloadsSummaryCard({ savedCount }: DownloadsSummaryCardProps) {
  return (
    <AppSectionCard
      title="Saved library"
      description="Saved stories live in your Buddybug account, so they are easy to reopen whenever you sign in."
    >
      <div className="rounded-2xl bg-slate-50 px-4 py-3">
        <div className="text-sm text-slate-500">Saved books</div>
        <div className="mt-1 text-2xl font-semibold text-slate-900">{savedCount}</div>
      </div>
      <Link
        href="/saved"
        className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
      >
        Open Saved Books
      </Link>
    </AppSectionCard>
  );
}
