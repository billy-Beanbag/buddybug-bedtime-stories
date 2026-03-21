"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ReadingPlanCard } from "@/components/ReadingPlanCard";
import { ReadingPlanForm, type ReadingPlanFormValues } from "@/components/ReadingPlanForm";
import { ReadingPlanSessionList } from "@/components/ReadingPlanSessionList";
import { ReadingPlanSuggestions } from "@/components/ReadingPlanSuggestions";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import type {
  ReadingPlanDetailResponse,
  ReadingPlanRead,
  ReadingPlanSessionRead,
  ReadingPlanSuggestionResponse,
} from "@/lib/types";

function toPayload(values: ReadingPlanFormValues) {
  return {
    child_profile_id: values.child_profile_id,
    title: values.title.trim(),
    description: values.description.trim() || null,
    status: values.status,
    plan_type: values.plan_type,
    preferred_age_band: values.preferred_age_band || null,
    preferred_language: values.preferred_language || null,
    preferred_content_lane_key: values.preferred_content_lane_key.trim() || null,
    prefer_narration: values.prefer_narration,
    sessions_per_week: values.sessions_per_week,
    target_days_csv: values.target_days_csv.trim() || null,
    bedtime_mode_preferred: values.bedtime_mode_preferred,
  };
}

export default function ReadingPlanDetailPage() {
  const params = useParams<{ planId: string }>();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { childProfiles, selectedChildProfile, isLoading: childrenLoading } = useChildProfiles();
  const [plan, setPlan] = useState<ReadingPlanRead | null>(null);
  const [sessions, setSessions] = useState<ReadingPlanSessionRead[]>([]);
  const [suggestions, setSuggestions] = useState<ReadingPlanSuggestionResponse["suggested_books"]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [archiving, setArchiving] = useState(false);
  const [completingSessionId, setCompletingSessionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadPlan(currentToken: string, planId: string) {
    const [detailResponse, suggestionsResponse] = await Promise.all([
      apiGet<ReadingPlanDetailResponse>(`/reading-plans/me/${planId}`, { token: currentToken }),
      apiGet<ReadingPlanSuggestionResponse>(`/reading-plans/me/${planId}/suggestions`, { token: currentToken }),
    ]);
    setPlan(detailResponse.plan);
    setSessions(detailResponse.upcoming_sessions);
    setSuggestions(suggestionsResponse.suggested_books);
  }

  useEffect(() => {
    if (authLoading || childrenLoading) {
      return;
    }
    if (!isAuthenticated || !token || !params.planId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    void loadPlan(token, params.planId)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load reading plan"))
      .finally(() => setLoading(false));
  }, [authLoading, childrenLoading, isAuthenticated, params.planId, token]);

  async function handleSave(values: ReadingPlanFormValues) {
    if (!token || !params.planId) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await apiPatch<ReadingPlanRead>(`/reading-plans/me/${params.planId}`, toPayload(values), { token });
      await loadPlan(token, params.planId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update reading plan");
    } finally {
      setSaving(false);
    }
  }

  async function handleComplete(sessionId: number) {
    if (!token || !params.planId) {
      return;
    }
    setCompletingSessionId(sessionId);
    setError(null);
    try {
      await apiPost<ReadingPlanSessionRead>(`/reading-plans/me/${params.planId}/sessions/${sessionId}/complete`, undefined, { token });
      await loadPlan(token, params.planId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to complete reading plan session");
    } finally {
      setCompletingSessionId(null);
    }
  }

  async function handleArchive() {
    if (!token || !params.planId) {
      return;
    }
    setArchiving(true);
    setError(null);
    try {
      await apiDelete<ReadingPlanRead>(`/reading-plans/me/${params.planId}`, { token });
      router.push("/reading-plans");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to archive reading plan");
    } finally {
      setArchiving(false);
    }
  }

  if (authLoading || childrenLoading || loading) {
    return <LoadingState message="Loading reading plan..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to see this reading plan"
          description="Reading plans are available for signed-in Buddybug family accounts."
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

  if (!plan) {
    return <EmptyState title="Reading plan unavailable" description={error || "This plan could not be loaded."} />;
  }

  return (
    <div className="space-y-4">
      {error ? <EmptyState title="Reading plan update failed" description={error} /> : null}

      <ReadingPlanCard plan={plan} childProfiles={childProfiles} />

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="space-y-3">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">Upcoming sessions</h3>
            <p className="mt-1 text-sm text-slate-600">
              These are soft routine prompts for the next few days, not a rigid calendar.
            </p>
          </div>
          <ReadingPlanSessionList
            sessions={sessions}
            completingSessionId={completingSessionId}
            onComplete={handleComplete}
          />
        </section>

        <section className="space-y-3">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">Suggested stories</h3>
            <p className="mt-1 text-sm text-slate-600">
              Suggestions stay aligned with the plan’s age, language, narration, and bedtime preferences.
            </p>
          </div>
          <ReadingPlanSuggestions suggestions={suggestions} />
        </section>
      </div>

      <ReadingPlanForm
        childProfiles={childProfiles}
        selectedChildProfileId={selectedChildProfile?.id || null}
        initialPlan={plan}
        submitting={saving}
        submitLabel="Save reading plan"
        onSubmit={handleSave}
      />

      <button
        type="button"
        onClick={() => void handleArchive()}
        disabled={archiving}
        className="w-full rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 disabled:opacity-60"
      >
        {archiving ? "Archiving..." : "Archive reading plan"}
      </button>
    </div>
  );
}
