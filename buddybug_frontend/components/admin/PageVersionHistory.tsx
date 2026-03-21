"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";
import type { RollbackResponse, StoryPageVersionRead } from "@/lib/types";

export function PageVersionHistory({
  pageId,
  token,
  pageNumber,
  onRolledBack,
}: {
  pageId: number;
  token: string | null;
  pageNumber: number;
  onRolledBack?: () => Promise<void> | void;
}) {
  const [versions, setVersions] = useState<StoryPageVersionRead[]>([]);
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
      const response = await apiGet<StoryPageVersionRead[]>(`/content-versions/story-pages/${pageId}`, { token });
      setVersions(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load page version history");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadVersions();
  }, [pageId, token]);

  return (
    <section className="space-y-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h4 className="text-base font-semibold text-slate-900">Page {pageNumber} history</h4>
          <p className="mt-1 text-sm text-slate-600">Roll back this page to a previous editorial snapshot if needed.</p>
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
      {loading ? <p className="text-sm text-slate-600">Loading page versions...</p> : null}
      {!loading && versions.length === 0 ? (
        <p className="text-sm text-slate-600">No page snapshots yet.</p>
      ) : null}

      <div className="space-y-3">
        {versions.map((version) => (
          <article key={version.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">Version {version.version_number}</p>
                <p className="text-xs text-slate-500">{new Date(version.created_at).toLocaleString()}</p>
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
                    `/content-versions/story-pages/${pageId}/rollback/${version.id}`,
                    undefined,
                    { token },
                  )
                    .then(async (response) => {
                      setMessage(response.message);
                      await loadVersions();
                      await onRolledBack?.();
                    })
                    .catch((err) => setError(err instanceof Error ? err.message : "Unable to roll back page"))
                    .finally(() => setRollingBackVersionId(null));
                }}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900 disabled:opacity-60"
              >
                {rollingBackVersionId === version.id ? "Rolling back..." : "Rollback"}
              </button>
            </div>
            <p className="mt-3 line-clamp-3 text-sm text-slate-600">{version.page_text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
