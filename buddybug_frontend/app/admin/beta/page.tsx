"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { BetaCohortEditor, type BetaCohortFormValue } from "@/components/admin/BetaCohortEditor";
import { BetaCohortTable } from "@/components/admin/BetaCohortTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { BetaCohortRead } from "@/lib/types";

function toPayload(value: BetaCohortFormValue) {
  return {
    ...value,
    description: value.description || null,
    feature_flag_keys: value.feature_flag_keys || null,
    notes: value.notes || null,
  };
}

export default function AdminBetaCohortsPage() {
  const { token, isAdmin } = useAuth();
  const [cohorts, setCohorts] = useState<BetaCohortRead[]>([]);
  const [selectedCohort, setSelectedCohort] = useState<BetaCohortRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadCohorts() {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await apiGet<BetaCohortRead[]>("/admin/beta-cohorts", { token });
      setCohorts(response);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load beta cohorts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadCohorts();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage beta cohorts." />;
  }

  if (loading) {
    return <LoadingState message="Loading beta cohorts..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Beta cohorts</h1>
        <p className="mt-2 text-sm text-slate-600">
          Group early-access users into simple cohorts so unfinished features can be staged safely before wider rollout.
        </p>
      </section>

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="space-y-4">
          {cohorts.length ? (
            <BetaCohortTable cohorts={cohorts} onEdit={(cohort) => setSelectedCohort(cohort)} />
          ) : (
            <EmptyState title="No beta cohorts yet" description="Create the first cohort to start staged previews." />
          )}
        </section>

        <BetaCohortEditor
          cohort={selectedCohort}
          submitting={saving}
          onSubmit={async (value) => {
            if (!token) {
              return;
            }
            setSaving(true);
            setStatusMessage(null);
            setErrorMessage(null);
            try {
              if (selectedCohort) {
                await apiPatch<BetaCohortRead>(`/admin/beta-cohorts/${selectedCohort.id}`, toPayload(value), { token });
                setStatusMessage(`Updated beta cohort "${value.name}".`);
              } else {
                await apiPost<BetaCohortRead>("/admin/beta-cohorts", toPayload(value), { token });
                setStatusMessage(`Created beta cohort "${value.name}".`);
              }
              setSelectedCohort(null);
              await loadCohorts();
            } catch (err) {
              setErrorMessage(err instanceof Error ? err.message : "Unable to save beta cohort");
            } finally {
              setSaving(false);
            }
          }}
          onCancel={selectedCohort ? () => setSelectedCohort(null) : undefined}
        />
      </div>
    </div>
  );
}
