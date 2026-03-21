"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { FamilyDigestCard } from "@/components/FamilyDigestCard";
import { FamilyDigestChildCard } from "@/components/FamilyDigestChildCard";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet, apiPost } from "@/lib/api";
import type {
  FamilyDigestDetailResponse,
  FamilyDigestGenerateResponse,
  FamilyDigestRead,
} from "@/lib/types";

interface FamilyDigestPayload {
  highlight_text?: string;
  try_next_text?: string;
  stories_opened?: number;
  stories_completed?: number;
  achievements_earned?: number;
  narration_uses?: number;
  saved_books_added?: number;
  completed_story_titles?: string[];
}

function parseSummary(summaryJson: string): FamilyDigestPayload {
  try {
    const parsed = JSON.parse(summaryJson) as FamilyDigestPayload;
    return parsed || {};
  } catch {
    return {};
  }
}

function formatDateRange(start: string, end: string) {
  const formatter = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
  return `${formatter.format(new Date(start))} - ${formatter.format(new Date(end))}`;
}

export default function FamilyDigestPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { childProfiles, selectedChildProfile, isLoading: childrenLoading } = useChildProfiles();
  const [latestDigest, setLatestDigest] = useState<FamilyDigestDetailResponse | null>(null);
  const [history, setHistory] = useState<FamilyDigestRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading || childrenLoading) {
      return;
    }
    if (!isAuthenticated || !token) {
      setLatestDigest(null);
      setHistory([]);
      setLoading(false);
      return;
    }

    async function loadDigest() {
      setLoading(true);
      setError(null);
      try {
        const [latestResponse, historyResponse] = await Promise.all([
          apiGet<FamilyDigestDetailResponse>("/family-digest/me/latest", { token }),
          apiGet<FamilyDigestRead[]>("/family-digest/me/history", { token, query: { limit: 12 } }),
        ]);
        setLatestDigest(latestResponse);
        setHistory(historyResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load family digest");
      } finally {
        setLoading(false);
      }
    }

    void loadDigest();
  }, [authLoading, childrenLoading, isAuthenticated, token]);

  const latestSummary = useMemo(
    () => (latestDigest ? parseSummary(latestDigest.digest.summary_json) : {}),
    [latestDigest],
  );

  async function handleRefreshDigest() {
    if (!token) {
      return;
    }
    setRefreshing(true);
    setError(null);
    try {
      const response = await apiPost<FamilyDigestGenerateResponse>("/family-digest/me/generate", undefined, { token });
      setLatestDigest({ digest: response.digest, child_summaries: response.child_summaries });
      const historyResponse = await apiGet<FamilyDigestRead[]>("/family-digest/me/history", { token, query: { limit: 12 } });
      setHistory(historyResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to refresh family digest");
    } finally {
      setRefreshing(false);
    }
  }

  if (authLoading || childrenLoading || loading) {
    return <LoadingState message="Loading family digest..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to see your family digest"
          description="Weekly Buddybug summaries are available for signed-in parent accounts."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white"
          >
            Create account
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Family digest</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          A calm weekly snapshot of Buddybug reading, narration, milestones, and gentle next steps for your family.
        </p>
        <button
          type="button"
          onClick={() => void handleRefreshDigest()}
          disabled={refreshing}
          className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
        >
          {refreshing ? "Refreshing..." : "Refresh weekly digest"}
        </button>
      </section>

      {error ? <EmptyState title="Unable to load family digest" description={error} /> : null}

      {latestDigest ? (
        <FamilyDigestCard
          digest={latestDigest.digest}
          highlightText={latestSummary.highlight_text || "A gentle family summary is ready."}
          tryNextText={latestSummary.try_next_text || "Keep story time simple with one calm read next week."}
          storiesOpened={latestSummary.stories_opened || 0}
          storiesCompleted={latestSummary.stories_completed || 0}
          achievementsEarned={latestSummary.achievements_earned || 0}
          narrationUses={latestSummary.narration_uses || 0}
          savedBooksAdded={latestSummary.saved_books_added || 0}
          completedStoryTitles={latestSummary.completed_story_titles || []}
        />
      ) : (
        <EmptyState
          title="No weekly digest yet"
          description="Buddybug will create a gentle family summary once there has been some reading activity."
        />
      )}

      <section className="space-y-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Child snapshots</h3>
          <p className="mt-1 text-sm text-slate-600">
            Child summaries stay high-level and encouraging, with a focus on routines rather than comparison.
          </p>
        </div>
        {latestDigest?.child_summaries.length ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {latestDigest.child_summaries.map((childSummary) => {
              const childProfile = childProfiles.find((item) => item.id === childSummary.child_profile_id);
              return (
                <FamilyDigestChildCard
                  key={childSummary.id}
                  childName={childProfile?.display_name || `Child ${childSummary.child_profile_id}`}
                  storiesOpened={childSummary.stories_opened}
                  storiesCompleted={childSummary.stories_completed}
                  narrationUses={childSummary.narration_uses}
                  achievementsEarned={childSummary.achievements_earned}
                  currentStreakDays={childSummary.current_streak_days}
                  summaryText={childSummary.summary_text}
                  highlighted={selectedChildProfile?.id === childSummary.child_profile_id}
                />
              );
            })}
          </div>
        ) : (
          <div className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4 text-sm text-slate-600">
            No child-specific activity was captured in this weekly window yet.
          </div>
        )}
      </section>

      <section className="space-y-3 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Previous weeks</h3>
          <p className="mt-1 text-sm text-slate-600">
            Earlier summaries stay available here and can later support weekly digest notifications or email delivery.
          </p>
        </div>
        {history.length ? (
          <div className="grid gap-3">
            {history.map((digest) => (
              <div key={digest.id} className="rounded-2xl bg-slate-50 px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-900">{digest.title}</p>
                    <p className="text-sm text-slate-500">{formatDateRange(digest.period_start, digest.period_end)}</p>
                  </div>
                  {latestDigest?.digest.id === digest.id ? (
                    <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700">Latest</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-600">Weekly digest history will appear here once summaries have been generated.</p>
        )}
      </section>
    </div>
  );
}
