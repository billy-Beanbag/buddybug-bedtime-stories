"use client";

import { useEffect, useState } from "react";

import { AccountHealthTable } from "@/components/admin/AccountHealthTable";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { AccountHealthSummaryResponse } from "@/lib/types";

export default function AdminAccountHealthPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<AccountHealthSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [rebuildingAll, setRebuildingAll] = useState(false);
  const [rebuildingUserId, setRebuildingUserId] = useState<number | null>(null);
  const [healthBand, setHealthBand] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function loadSummary(selectedBand = healthBand) {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<AccountHealthSummaryResponse>("/admin/account-health", {
        token,
        query: {
          health_band: selectedBand || undefined,
          limit: 100,
        },
      });
      setSummary(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load account health");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadSummary();
    }
  }, [token]);

  if (loading) {
    return <LoadingState message="Loading account health..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Account health</h1>
            <p className="mt-1 text-sm text-slate-600">
              Practical customer-success signals for spotting healthy accounts, watchlist users, and churn risk.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              if (!token) {
                return;
              }
              setRebuildingAll(true);
              setError(null);
              void apiPost<AccountHealthSummaryResponse>("/admin/account-health/rebuild-all", undefined, { token })
                .then((response) => setSummary(response))
                .catch((err) => setError(err instanceof Error ? err.message : "Unable to rebuild account health"))
                .finally(() => setRebuildingAll(false));
            }}
            disabled={rebuildingAll}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {rebuildingAll ? "Rebuilding all..." : "Rebuild all"}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-slate-700" htmlFor="health-band-filter">
            Health band
          </label>
          <select
            id="health-band-filter"
            value={healthBand}
            onChange={(event) => {
              const nextBand = event.target.value;
              setHealthBand(nextBand);
              void loadSummary(nextBand);
            }}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All</option>
            <option value="healthy">Healthy</option>
            <option value="watch">Watch</option>
            <option value="at_risk">At risk</option>
            <option value="churned">Churned</option>
          </select>
          {summary ? <span className="text-sm text-slate-500">{summary.total} snapshots</span> : null}
        </div>
      </section>

      {error ? <EmptyState title="Account health unavailable" description={error} /> : null}

      {!summary || summary.items.length === 0 ? (
        <EmptyState
          title="No account health snapshots yet"
          description="Run a rebuild to generate the first customer success view."
        />
      ) : (
        <AccountHealthTable
          items={summary.items}
          rebuildingUserId={rebuildingUserId}
          onRebuild={async (userId) => {
            if (!token) {
              return;
            }
            setRebuildingUserId(userId);
            setError(null);
            try {
              await apiPost(`/admin/account-health/${userId}/rebuild`, undefined, { token });
              await loadSummary();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Unable to rebuild user snapshot");
            } finally {
              setRebuildingUserId(null);
            }
          }}
        />
      )}
    </div>
  );
}
