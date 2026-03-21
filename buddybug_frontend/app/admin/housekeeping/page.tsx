"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { HousekeepingPolicyTable } from "@/components/admin/HousekeepingPolicyTable";
import { HousekeepingRunTable } from "@/components/admin/HousekeepingRunTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type {
  HousekeepingPolicyRead,
  HousekeepingRunRead,
  HousekeepingRunResponse,
  HousekeepingSummaryResponse,
} from "@/lib/types";

export default function AdminHousekeepingPage() {
  const { token, isAdmin } = useAuth();
  const [policies, setPolicies] = useState<HousekeepingPolicyRead[]>([]);
  const [runs, setRuns] = useState<HousekeepingRunRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [runningPolicyId, setRunningPolicyId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [targetTable, setTargetTable] = useState("notification_events");
  const [actionType, setActionType] = useState("report_only");
  const [retentionDays, setRetentionDays] = useState("90");
  const [enabled, setEnabled] = useState(true);
  const [dryRunOnly, setDryRunOnly] = useState(true);
  const [notes, setNotes] = useState("");

  async function loadSummary() {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await apiGet<HousekeepingSummaryResponse>("/admin/housekeeping/summary", { token });
      setPolicies(response.policies);
      setRuns(response.recent_runs);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load housekeeping summary");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadSummary();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage housekeeping policies." />;
  }

  if (loading) {
    return <LoadingState message="Loading housekeeping policies..." />;
  }

  async function handleRun(policy: HousekeepingPolicyRead, dryRunOverride?: boolean) {
    if (!token) {
      return;
    }
    setRunningPolicyId(policy.id);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const suffix = dryRunOverride === undefined ? "" : `?dry_run=${dryRunOverride ? "true" : "false"}`;
      const response = await apiPost<HousekeepingRunResponse>(`/admin/housekeeping/policies/${policy.id}/run${suffix}`, undefined, { token });
      setStatusMessage(
        response.run.status === "succeeded"
          ? `Housekeeping policy "${policy.name}" completed with ${response.run.candidate_count} candidates.`
          : `Housekeeping policy "${policy.name}" finished with status ${response.run.status}.`,
      );
      await loadSummary();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to run housekeeping policy");
    } finally {
      setRunningPolicyId(null);
    }
  }

  async function handleCreate() {
    if (!token) {
      return;
    }
    setCreating(true);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const created = await apiPost<HousekeepingPolicyRead>(
        "/admin/housekeeping/policies",
        {
          key,
          name,
          target_table: targetTable,
          action_type: actionType,
          retention_days: Number(retentionDays),
          enabled,
          dry_run_only: dryRunOnly,
          notes: notes || null,
        },
        { token },
      );
      setStatusMessage(`Created housekeeping policy "${created.name}".`);
      setKey("");
      setName("");
      setNotes("");
      await loadSummary();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to create housekeeping policy");
    } finally {
      setCreating(false);
    }
  }

  async function togglePolicy(policy: HousekeepingPolicyRead, nextEnabled: boolean) {
    if (!token) {
      return;
    }
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      await apiPatch(`/admin/housekeeping/policies/${policy.id}`, { enabled: nextEnabled }, { token });
      setStatusMessage(`${nextEnabled ? "Enabled" : "Disabled"} policy "${policy.name}".`);
      await loadSummary();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to update housekeeping policy");
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Housekeeping</h1>
        <p className="mt-2 text-sm text-slate-600">
          Review safe cleanup candidates, run dry-run retention analysis, and keep operational tables healthy without touching critical user or billing data.
        </p>
      </section>

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          {policies.length ? (
            <>
              <HousekeepingPolicyTable policies={policies} runningPolicyId={runningPolicyId} onRun={handleRun} />
              <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900">Quick toggles</h3>
                <div className="mt-4 flex flex-wrap gap-3">
                  {policies.map((policy) => (
                    <button
                      key={policy.id}
                      type="button"
                      onClick={() => void togglePolicy(policy, !policy.enabled)}
                      className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
                    >
                      {policy.enabled ? "Disable" : "Enable"} {policy.key}
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <EmptyState title="No housekeeping policies yet" description="Create the first policy or rely on seeded defaults after migrations and startup seeding." />
          )}

          <section className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Recent runs</h2>
              <p className="mt-1 text-sm text-slate-600">Dry-run output and safe cleanup history for the most recent housekeeping activity.</p>
            </div>
            {runs.length ? <HousekeepingRunTable runs={runs} /> : <EmptyState title="No housekeeping runs yet" description="Run a policy to generate cleanup analysis." />}
          </section>
        </div>

        <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Create policy</h2>
            <p className="mt-1 text-sm text-slate-600">Define a bounded housekeeping policy for supported operational tables only.</p>
          </div>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Key</span>
            <input value={key} onChange={(event) => setKey(event.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900" />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900" />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Target table</span>
            <select value={targetTable} onChange={(event) => setTargetTable(event.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900">
              <option value="notification_events">notification_events</option>
              <option value="reengagement_suggestions">reengagement_suggestions</option>
              <option value="maintenance_jobs">maintenance_jobs</option>
              <option value="workflow_jobs">workflow_jobs</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Action type</span>
            <select value={actionType} onChange={(event) => setActionType(event.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900">
              <option value="report_only">report_only</option>
              <option value="archive_flag">archive_flag</option>
              <option value="soft_cleanup">soft_cleanup</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Retention days</span>
            <input
              type="number"
              min={1}
              value={retentionDays}
              onChange={(event) => setRetentionDays(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Notes</span>
            <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900" />
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} />
            Enabled
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" checked={dryRunOnly} onChange={(event) => setDryRunOnly(event.target.checked)} />
            Dry-run only
          </label>
          <button
            type="button"
            onClick={() => void handleCreate()}
            disabled={creating || !key.trim() || !name.trim() || !retentionDays.trim()}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {creating ? "Creating..." : "Create policy"}
          </button>
        </section>
      </div>
    </div>
  );
}
