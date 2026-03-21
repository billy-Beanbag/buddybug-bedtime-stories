"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AchievementGrid } from "@/components/AchievementGrid";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { NextMilestoneCard } from "@/components/NextMilestoneCard";
import { ReadingStreakCard } from "@/components/ReadingStreakCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet, apiPost } from "@/lib/api";
import type { AchievementDashboardResponse } from "@/lib/types";

export default function AchievementsPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { selectedChildProfile, isLoading: childProfilesLoading } = useChildProfiles();
  const [dashboard, setDashboard] = useState<AchievementDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading || childProfilesLoading) {
      return;
    }
    if (!isAuthenticated || !token) {
      setDashboard(null);
      setLoading(false);
      return;
    }

    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiGet<AchievementDashboardResponse>("/achievements/me", {
          token,
          query: { child_profile_id: selectedChildProfile?.id },
        });
        setDashboard(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load achievements");
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, [authLoading, childProfilesLoading, isAuthenticated, selectedChildProfile?.id, token]);

  async function handleRebuild() {
    if (!token) {
      return;
    }
    setRebuilding(true);
    setError(null);
    try {
      const response = await apiPost<AchievementDashboardResponse>("/achievements/me/rebuild", undefined, {
        token,
        query: { child_profile_id: selectedChildProfile?.id },
      });
      setDashboard(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to refresh achievements");
    } finally {
      setRebuilding(false);
    }
  }

  if (authLoading || childProfilesLoading || loading) {
    return <LoadingState message="Loading achievements..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to see achievements"
          description="Achievements and reading streaks are available for signed-in family accounts."
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

  const scopeLabel = selectedChildProfile ? `${selectedChildProfile.display_name}'s progress` : "family progress";

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Achievements</h2>
        <p className="mt-2 text-sm text-slate-600">
          Calm encouragement for reading routines, saved stories, and small family milestones.
        </p>
        <p className="mt-3 text-sm text-indigo-700">
          Viewing: {scopeLabel}
        </p>
        <button
          type="button"
          onClick={() => void handleRebuild()}
          disabled={rebuilding}
          className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
        >
          {rebuilding ? "Refreshing..." : "Refresh progress"}
        </button>
      </section>

      {error ? <EmptyState title="Unable to load achievements" description={error} /> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <ReadingStreakCard
          currentStreak={dashboard?.current_streak || 0}
          longestStreak={dashboard?.longest_streak || 0}
          scopeLabel={scopeLabel}
        />
        <NextMilestoneCard
          milestoneTitle={dashboard?.next_suggested_milestone || null}
          scopeLabel={scopeLabel}
        />
      </div>

      <section className="space-y-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Earned moments</h3>
          <p className="mt-1 text-sm text-slate-600">
            Gentle milestones are saved here for parents and children to revisit together.
          </p>
        </div>
        <AchievementGrid achievements={dashboard?.earned_achievements || []} />
      </section>
    </div>
  );
}
