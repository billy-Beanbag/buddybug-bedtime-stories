"use client";

import { useState } from "react";

import { apiPost } from "@/lib/api";
import type { AdminAudioSummary } from "@/lib/types";

export function AudioQueueList({
  audioItems,
  token,
  onUpdated,
}: {
  audioItems: AdminAudioSummary[];
  token: string | null;
  onUpdated: () => Promise<void> | void;
}) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function handleAction(audioId: number, action: "approve" | "reject" | "activate") {
    if (!token) {
      return;
    }

    setBusyId(audioId);
    setMessage(null);
    setError(null);
    try {
      const payload = action === "approve" ? { make_active: true } : undefined;
      await apiPost(`/audio/books/${audioId}/${action}`, payload, { token });
      setMessage(`Audio ${action}d.`);
      await onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Unable to ${action} audio`);
    } finally {
      setBusyId(null);
    }
  }

  if (!audioItems.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        No audio items are waiting in this queue.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {audioItems.map((audio) => (
        <div key={audio.id} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Audio #{audio.id}</h3>
              <p className="mt-1 text-sm text-slate-600">
                Book {audio.book_id} • Voice {audio.voice_id}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                Status: {audio.approval_status} • Active: {audio.is_active ? "Yes" : "No"}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busyId === audio.id}
                onClick={() => handleAction(audio.id, "approve")}
                className="rounded-2xl bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 disabled:opacity-60"
              >
                Approve
              </button>
              <button
                type="button"
                disabled={busyId === audio.id}
                onClick={() => handleAction(audio.id, "reject")}
                className="rounded-2xl bg-rose-50 px-4 py-2 text-sm font-medium text-rose-800 disabled:opacity-60"
              >
                Reject
              </button>
              <button
                type="button"
                disabled={busyId === audio.id}
                onClick={() => handleAction(audio.id, "activate")}
                className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-medium text-slate-800 disabled:opacity-60"
              >
                Activate
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
