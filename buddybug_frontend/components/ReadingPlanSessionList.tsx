"use client";

import type { ReadingPlanSessionRead } from "@/lib/types";

interface ReadingPlanSessionListProps {
  sessions: ReadingPlanSessionRead[];
  completingSessionId?: number | null;
  onComplete?: (sessionId: number) => Promise<void> | void;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

export function ReadingPlanSessionList({
  sessions,
  completingSessionId = null,
  onComplete,
}: ReadingPlanSessionListProps) {
  if (!sessions.length) {
    return (
      <div className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4 text-sm text-slate-600">
        No upcoming sessions have been lined up yet.
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {sessions.map((item) => (
        <div key={item.id} className="rounded-[2rem] border border-white/70 bg-white/85 p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-slate-900">{formatDate(item.scheduled_date)}</p>
              <p className="mt-1 text-sm text-slate-600">
                {item.suggested_book_id ? `Suggested story #${item.suggested_book_id}` : "Story suggestion coming soon"}
              </p>
            </div>
            {item.completed ? (
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">Completed</span>
            ) : onComplete ? (
              <button
                type="button"
                onClick={() => void onComplete(item.id)}
                disabled={completingSessionId === item.id}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
              >
                {completingSessionId === item.id ? "Saving..." : "Mark complete"}
              </button>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
