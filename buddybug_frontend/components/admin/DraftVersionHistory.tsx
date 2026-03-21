"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";
import type { RollbackResponse, StoryDraftVersionRead } from "@/lib/types";

export function DraftVersionHistory({
  draftId,
  token,
  onRolledBack,
}: {
  draftId: number;
  token: string | null;
  onRolledBack?: () => Promise<void> | void;
}) {
  const [versions, setVersions] = useState<StoryDraftVersionRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rollingBackVersionId, setRollingBackVersionId] = useState<number | null>(null);

  async function loadVersions() {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<StoryDraftVersionRead[]>(`/content-versions/story-drafts/${draftId}`, { token });
      setVersions(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load draft version history");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadVersions();
  }, [draftId, token]);

  return (
    <section className="space-y-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Draft version history</h3>
          <p className="mt-1 text-sm text-slate-600">Each save snapshots the previous draft state so editors can roll back safely.</p>
        </div>
        <button
          type="button"
          onClick={() => void loadVersions()}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900"
        >
          Refresh
        </button>
      </div>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {loading ? <p className="text-sm text-slate-600">Loading version history...</p> : null}
      {!loading && versions.length === 0 ? (
        <p className="text-sm text-slate-600">No draft snapshots yet. The first version appears after an edit or rollback.</p>
      ) : null}

      <div className="space-y-3">
        {versions.map((version) => (
          <article key={version.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">
                  Version {version.version_number} • {version.title}
                </p>
                <p className="text-xs text-slate-500">{new Date(version.created_at).toLocaleString()}</p>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{version.review_status}</p>
              </div>
              <button
                type="button"
                disabled={rollingBackVersionId === version.id}
                onClick={() => {
                  if (!token) {
                    return;
                  }
                  setRollingBackVersionId(version.id);
                  setMessage(null);
                  setError(null);
                  void apiPost<RollbackResponse>(
                    `/content-versions/story-drafts/${draftId}/rollback/${version.id}`,
                    undefined,
                    { token },
                  )
                    .then(async (response) => {
                      setMessage(response.message);
                      await loadVersions();
                      await onRolledBack?.();
                    })
                    .catch((err) => setError(err instanceof Error ? err.message : "Unable to roll back draft"))
                    .finally(() => setRollingBackVersionId(null));
                }}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900 disabled:opacity-60"
              >
                {rollingBackVersionId === version.id ? "Rolling back..." : "Rollback"}
              </button>
            </div>
            <p className="mt-3 line-clamp-3 text-sm text-slate-600">{version.summary}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
