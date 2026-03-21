"use client";

import Link from "next/link";

import { AppSectionCard } from "@/components/AppSectionCard";

interface DownloadsSummaryCardProps {
  offlineCount: number;
  savedCount: number;
}

export function DownloadsSummaryCard({ offlineCount, savedCount }: DownloadsSummaryCardProps) {
  return (
    <AppSectionCard
      title="Downloads and offline reading"
      description="Keep track of what is saved in your library versus what is cached on this device."
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-sm text-slate-500">Saved books</div>
          <div className="mt-1 text-2xl font-semibold text-slate-900">{savedCount}</div>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-sm text-slate-500">Available offline here</div>
          <div className="mt-1 text-2xl font-semibold text-slate-900">{offlineCount}</div>
        </div>
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
