"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ReadingPlanCard } from "@/components/ReadingPlanCard";
import { ReadingPlanForm, type ReadingPlanFormValues } from "@/components/ReadingPlanForm";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet, apiPost } from "@/lib/api";
import type { ReadingPlanRead } from "@/lib/types";

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

export default function ReadingPlansPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { childProfiles, selectedChildProfile, isLoading: childrenLoading } = useChildProfiles();
  const [plans, setPlans] = useState<ReadingPlanRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadPlans(currentToken: string) {
    const response = await apiGet<ReadingPlanRead[]>("/reading-plans/me", { token: currentToken });
    setPlans(response);
  }

  useEffect(() => {
    if (authLoading || childrenLoading) {
      return;
    }
    if (!isAuthenticated || !token) {
      setPlans([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    void loadPlans(token)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load reading plans"))
      .finally(() => setLoading(false));
  }, [authLoading, childrenLoading, isAuthenticated, token]);

  async function handleCreate(values: ReadingPlanFormValues) {
    if (!token) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await apiPost<ReadingPlanRead>("/reading-plans/me", toPayload(values), { token });
      await loadPlans(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create reading plan");
    } finally {
      setSubmitting(false);
    }
  }

  if (authLoading || childrenLoading || loading) {
    return <LoadingState message="Loading reading plans..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to build reading plans"
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

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Reading plans</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Build a gentle routine for bedtime, narration nights, language practice, or simple family story moments.
        </p>
      </section>

      {error ? <EmptyState title="Unable to load reading plans" description={error} /> : null}

      <ReadingPlanForm
        childProfiles={childProfiles}
        selectedChildProfileId={selectedChildProfile?.id || null}
        submitting={submitting}
        submitLabel="Create reading plan"
        onSubmit={handleCreate}
      />

      <section className="space-y-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Current plans</h3>
          <p className="mt-1 text-sm text-slate-600">Plans stay flexible, so families can follow the rhythm that feels right.</p>
        </div>
        {plans.length ? (
          <div className="grid gap-4">
            {plans.map((plan) => (
              <ReadingPlanCard key={plan.id} plan={plan} childProfiles={childProfiles} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No reading plans yet"
            description="Create the first plan to turn story time into a calmer weekly rhythm."
          />
        )}
      </section>
    </div>
  );
}
