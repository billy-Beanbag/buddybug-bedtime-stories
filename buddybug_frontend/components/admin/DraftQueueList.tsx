"use client";

import Link from "next/link";

import type { AdminStoryDraftSummary } from "@/lib/types";

export function DraftQueueList({ drafts }: { drafts: AdminStoryDraftSummary[] }) {
  if (!drafts.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        No drafts are currently waiting for review.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {drafts.map((draft) => (
        <Link
          key={draft.id}
          href={`/admin/drafts/${draft.id}`}
          className="block rounded-3xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md"
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <h3 className="text-base font-semibold text-slate-900">{draft.title}</h3>
              <p className="mt-1 line-clamp-2 text-sm text-slate-600">{draft.summary}</p>
            </div>
            <div className="shrink-0 space-y-2 text-right text-sm">
              <div className="rounded-full bg-amber-50 px-3 py-1 font-medium text-amber-700">
                {draft.review_status}
              </div>
              <p className="text-slate-500">{draft.read_time_minutes} min</p>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
