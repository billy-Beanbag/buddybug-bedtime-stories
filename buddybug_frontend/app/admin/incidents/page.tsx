"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { IncidentTable } from "@/components/admin/IncidentTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { IncidentRecordRead, IncidentSummaryResponse } from "@/lib/types";

const EMPTY_SUMMARY: IncidentSummaryResponse = {
  open_incidents: 0,
  sev_1_open: 0,
  sev_2_open: 0,
  incidents_resolved_30d: 0,
};

export default function AdminIncidentsPage() {
  const { token, isAdmin } = useAuth();
  const [incidents, setIncidents] = useState<IncidentRecordRead[]>([]);
  const [summary, setSummary] = useState<IncidentSummaryResponse>(EMPTY_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [areaFilter, setAreaFilter] = useState("");
  const [title, setTitle] = useState("");
  const [summaryText, setSummaryText] = useState("");
  const [severity, setSeverity] = useState("sev_2");
  const [affectedArea, setAffectedArea] = useState("content_pipeline");
  const [customerImpactSummary, setCustomerImpactSummary] = useState("");
  const [featureFlagKey, setFeatureFlagKey] = useState("");

  async function loadIncidents(nextSeverity = severityFilter, nextStatus = statusFilter, nextArea = areaFilter) {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const [incidentResponse, summaryResponse] = await Promise.all([
        apiGet<IncidentRecordRead[]>("/admin/incidents", {
          token,
          query: {
            severity: nextSeverity || undefined,
            status: nextStatus || undefined,
            affected_area: nextArea || undefined,
            limit: 100,
          },
        }),
        apiGet<IncidentSummaryResponse>("/admin/incidents/summary", { token }),
      ]);
      setIncidents(incidentResponse);
      setSummary(summaryResponse);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load incidents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadIncidents();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage incidents and runbooks." />;
  }

  if (loading) {
    return <LoadingState message="Loading incident console..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Incident console</h1>
        <p className="mt-2 text-sm text-slate-600">
          Track active production issues, severity, customer impact, mitigation updates, and post-incident handoff details.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Open incidents</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{summary.open_incidents}</p>
          </div>
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4">
            <p className="text-sm text-rose-700">SEV-1 open</p>
            <p className="mt-2 text-2xl font-semibold text-rose-900">{summary.sev_1_open}</p>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm text-amber-700">SEV-2 open</p>
            <p className="mt-2 text-2xl font-semibold text-amber-900">{summary.sev_2_open}</p>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="text-sm text-emerald-700">Resolved in 30d</p>
            <p className="mt-2 text-2xl font-semibold text-emerald-900">{summary.incidents_resolved_30d}</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={severityFilter}
            onChange={(event) => setSeverityFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All severities</option>
            <option value="sev_1">sev_1</option>
            <option value="sev_2">sev_2</option>
            <option value="sev_3">sev_3</option>
            <option value="sev_4">sev_4</option>
          </select>
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="investigating">investigating</option>
            <option value="identified">identified</option>
            <option value="monitoring">monitoring</option>
            <option value="resolved">resolved</option>
            <option value="canceled">canceled</option>
          </select>
          <input
            value={areaFilter}
            onChange={(event) => setAreaFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="Filter by area"
          />
          <button
            type="button"
            onClick={() => void loadIncidents(severityFilter, statusFilter, areaFilter)}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
          >
            Apply filters
          </button>
        </div>
      </section>

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div>
          {incidents.length ? (
            <IncidentTable incidents={incidents} />
          ) : (
            <EmptyState title="No incidents match these filters" description="Adjust the filters or create a new incident record." />
          )}
        </div>

        <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Log new incident</h2>
          <p className="mt-1 text-sm text-slate-600">Capture the issue early, then use the detail page for timeline notes and resolution handling.</p>
          <div className="mt-4 grid gap-4">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Title</span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                placeholder="Story generation pipeline failures"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Summary</span>
              <textarea
                value={summaryText}
                onChange={(event) => setSummaryText(event.target.value)}
                rows={4}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                placeholder="What is failing, how it was detected, and why this matters right now"
              />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Severity</span>
                <select
                  value={severity}
                  onChange={(event) => setSeverity(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                >
                  <option value="sev_1">sev_1</option>
                  <option value="sev_2">sev_2</option>
                  <option value="sev_3">sev_3</option>
                  <option value="sev_4">sev_4</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Affected area</span>
                <input
                  value={affectedArea}
                  onChange={(event) => setAffectedArea(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                  placeholder="content_pipeline"
                />
              </label>
            </div>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Customer impact</span>
              <textarea
                value={customerImpactSummary}
                onChange={(event) => setCustomerImpactSummary(event.target.value)}
                rows={3}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                placeholder="Optional customer-facing impact summary"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Feature flag key</span>
              <input
                value={featureFlagKey}
                onChange={(event) => setFeatureFlagKey(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                placeholder="Optional flag key"
              />
            </label>
            <button
              type="button"
              disabled={creating || !title.trim() || !summaryText.trim() || !affectedArea.trim()}
              onClick={() => {
                if (!token) {
                  return;
                }
                setCreating(true);
                setStatusMessage(null);
                setErrorMessage(null);
                void apiPost<IncidentRecordRead>(
                  "/admin/incidents",
                  {
                    title,
                    summary: summaryText,
                    severity,
                    affected_area: affectedArea,
                    feature_flag_key: featureFlagKey || null,
                    customer_impact_summary: customerImpactSummary || null,
                  },
                  { token },
                )
                  .then(async (created) => {
                    setTitle("");
                    setSummaryText("");
                    setCustomerImpactSummary("");
                    setFeatureFlagKey("");
                    setSeverity("sev_2");
                    setAffectedArea("content_pipeline");
                    setStatusMessage(`Created incident #${created.id}.`);
                    await loadIncidents();
                  })
                  .catch((err: unknown) => {
                    setErrorMessage(err instanceof Error ? err.message : "Unable to create incident");
                  })
                  .finally(() => {
                    setCreating(false);
                  });
              }}
              className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
            >
              {creating ? "Creating..." : "Create incident"}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
