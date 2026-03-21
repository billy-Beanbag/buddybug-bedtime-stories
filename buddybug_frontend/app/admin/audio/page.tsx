"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { AudioQueueList } from "@/components/admin/AudioQueueList";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { AdminAudioSummary } from "@/lib/types";

export default function AdminAudioPage() {
  const { token } = useAuth();
  const [audioItems, setAudioItems] = useState<AdminAudioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approvalStatus, setApprovalStatus] = useState("");

  async function loadAudio() {
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<AdminAudioSummary[]>("/admin/audio/queue", {
        token,
        query: { approval_status: approvalStatus || undefined },
      });
      setAudioItems(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load audio queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAudio();
  }, [token, approvalStatus]);

  if (loading) {
    return <LoadingState message="Loading audio queue..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load audio queue" description={error} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Audio queue</h2>
          <p className="mt-1 text-sm text-slate-600">Approve, reject, or activate narration assets.</p>
        </div>
        <div className="flex gap-2">
          <select
            value={approvalStatus}
            onChange={(event) => setApprovalStatus(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="generated">Generated</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button
            type="button"
            onClick={() => void loadAudio()}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Refresh
          </button>
        </div>
      </div>

      <AudioQueueList audioItems={audioItems} token={token} onUpdated={loadAudio} />
    </div>
  );
}
