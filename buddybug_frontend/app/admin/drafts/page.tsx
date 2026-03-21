"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { DraftQueueList } from "@/components/admin/DraftQueueList";
import { ReadyForPlanningList } from "@/components/admin/ReadyForPlanningList";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { AdminStoryDraftSummary } from "@/lib/types";

export default function AdminDraftsPage() {
  const { token } = useAuth();
  const [drafts, setDrafts] = useState<AdminStoryDraftSummary[]>([]);
  const [readyDrafts, setReadyDrafts] = useState<AdminStoryDraftSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewStatus, setReviewStatus] = useState("");

  async function loadDrafts() {
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [queueResponse, readyResponse] = await Promise.all([
        apiGet<AdminStoryDraftSummary[]>("/admin/drafts/queue", {
          token,
          query: { review_status: reviewStatus || undefined },
        }),
        apiGet<AdminStoryDraftSummary[]>("/admin/drafts/ready-for-planning", { token }),
      ]);
      setDrafts(queueResponse);
      setReadyDrafts(readyResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load drafts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDrafts();
  }, [token, reviewStatus]);

  if (loading) {
    return <LoadingState message="Loading draft queues..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load drafts" description={error} />;
  }

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Draft review queue</h2>
            <p className="mt-1 text-sm text-slate-600">Drafts currently waiting for review or revision work.</p>
          </div>
          <div className="flex gap-2">
            <select
              value={reviewStatus}
              onChange={(event) => setReviewStatus(event.target.value)}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            >
            <option value="">All statuses</option>
              <option value="draft_pending_review">Draft pending review</option>
              <option value="review_pending">Review pending</option>
              <option value="needs_revision">Needs revision</option>
              <option value="approved_for_illustration">Approved for illustration</option>
              <option value="rejected">Rejected</option>
            </select>
            <button
              type="button"
              onClick={() => void loadDrafts()}
              className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
            >
              Refresh
            </button>
          </div>
        </div>
        <DraftQueueList drafts={drafts} />
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Ready for illustration planning</h2>
          <p className="mt-1 text-sm text-slate-600">Approved drafts that do not yet have generated story pages.</p>
        </div>
        <ReadyForPlanningList drafts={readyDrafts} />
      </section>
    </div>
  );
}
