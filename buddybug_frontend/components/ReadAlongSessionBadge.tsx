"use client";

import type { ReadAlongDetailResponse } from "@/lib/types";

function formatRelativeSessionTime(value: string) {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return "just now";
  }

  const diffMs = Math.max(0, Date.now() - parsed);
  const diffMinutes = Math.round(diffMs / 60000);
  if (diffMinutes < 1) {
    return "just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  const diffDays = Math.round(diffHours / 24);
  return `${diffDays}d ago`;
}

export function ReadAlongSessionBadge({
  detail,
  compact = false,
}: {
  detail: ReadAlongDetailResponse;
  compact?: boolean;
}) {
  const { session, participants } = detail;

  return (
    <div
      className={`rounded-2xl border border-indigo-200 bg-indigo-50/90 text-indigo-950 shadow-sm ${
        compact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-white px-2 py-1 font-semibold text-indigo-700">Read together</span>
        <span>Code {session.join_code}</span>
        <span>Page {session.current_page_number}</span>
        <span>{participants.length} participant{participants.length === 1 ? "" : "s"}</span>
        <span className="capitalize">{session.playback_state.replace("_", " ")}</span>
      </div>
      {!compact ? (
        <p className="mt-2 text-xs text-indigo-800">
          Last updated {formatRelativeSessionTime(session.updated_at)}. Shared syncing stays private to this account.
        </p>
      ) : null}
    </div>
  );
}
