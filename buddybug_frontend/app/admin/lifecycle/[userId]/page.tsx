"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { LifecycleSummaryCard } from "@/components/admin/LifecycleSummaryCard";
import { LifecycleTimeline } from "@/components/admin/LifecycleTimeline";
import { RebuildLifecycleButton } from "@/components/admin/RebuildLifecycleButton";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { LifecycleRebuildResponse, LifecycleSummaryResponse, LifecycleTimelineResponse } from "@/lib/types";

export default function AdminLifecyclePage() {
  const params = useParams<{ userId: string }>();
  const userId = Number(params.userId);
  const { token, isAdmin } = useAuth();
  const [summary, setSummary] = useState<LifecycleSummaryResponse | null>(null);
  const [timeline, setTimeline] = useState<LifecycleTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadLifecycle() {
    if (!token || !userId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [summaryResponse, timelineResponse] = await Promise.all([
        apiGet<LifecycleSummaryResponse>(`/admin/lifecycle/users/${userId}/summary`, { token }),
        apiGet<LifecycleTimelineResponse>(`/admin/lifecycle/users/${userId}`, { token }),
      ]);
      setSummary(summaryResponse);
      setTimeline(timelineResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load lifecycle timeline");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadLifecycle();
    }
  }, [token, userId]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can review lifecycle timelines." />;
  }

  if (loading) {
    return <LoadingState message="Loading lifecycle timeline..." />;
  }

  if (error || !summary || !timeline) {
    return <EmptyState title="Unable to load lifecycle timeline" description={error || "Lifecycle data is unavailable."} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">Subscriber lifecycle</p>
          <h1 className="text-2xl font-semibold text-slate-900">User #{userId}</h1>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/admin/account-health"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
          >
            Account health
          </Link>
          <RebuildLifecycleButton
            rebuilding={rebuilding}
            onRebuild={async () => {
              if (!token) {
                return;
              }
              setRebuilding(true);
              setError(null);
              setStatusMessage(null);
              try {
                const response = await apiPost<LifecycleRebuildResponse>(`/admin/lifecycle/users/${userId}/rebuild`, undefined, {
                  token,
                });
                setTimeline({ user_id: userId, milestones: response.milestones });
                setStatusMessage(`Rebuilt lifecycle milestones. ${response.created_count} new milestones were created.`);
                const refreshedSummary = await apiGet<LifecycleSummaryResponse>(`/admin/lifecycle/users/${userId}/summary`, { token });
                setSummary(refreshedSummary);
              } catch (err) {
                setError(err instanceof Error ? err.message : "Unable to rebuild lifecycle");
              } finally {
                setRebuilding(false);
              }
            }}
          />
        </div>
      </div>

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {error ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}

      <LifecycleSummaryCard summary={summary} />
      <LifecycleTimeline milestones={timeline.milestones} />
    </div>
  );
}
