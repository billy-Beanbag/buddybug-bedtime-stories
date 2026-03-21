"use client";

import Link from "next/link";

import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { AdminStoryDraftSummary } from "@/lib/types";

export function ReadyForPlanningList({
  drafts,
}: {
  drafts: AdminStoryDraftSummary[];
}) {
  if (!drafts.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        No approved drafts are waiting for illustration planning.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {drafts.map((draft) => (
        <div key={draft.id} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <h3 className="text-base font-semibold text-slate-900">{draft.title}</h3>
              <p className="mt-1 text-sm text-slate-600">{draft.summary}</p>
            </div>
            <div className="shrink-0">
              <Link
                href={`/admin/story-pages?draftId=${draft.id}`}
                className={`inline-flex rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
              >
                Open planning queue
              </Link>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
