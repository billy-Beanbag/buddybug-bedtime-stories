"use client";

import { useEffect, useState } from "react";

import type { IncidentDetailResponse, RunbookEntryRead } from "@/lib/types";

import { IncidentUpdateForm } from "./IncidentUpdateForm";

export function IncidentDetail({
  detail,
  relatedRunbooks,
  onUpdate,
  onResolve,
  onAddUpdate,
}: {
  detail: IncidentDetailResponse;
  relatedRunbooks: RunbookEntryRead[];
  onUpdate: (payload: Record<string, unknown>) => Promise<void>;
  onResolve: (resolutionNote: string) => Promise<void>;
  onAddUpdate: (payload: { update_type: string; body: string }) => Promise<void>;
}) {
  const [title, setTitle] = useState(detail.incident.title);
  const [summary, setSummary] = useState(detail.incident.summary);
  const [severity, setSeverity] = useState(detail.incident.severity);
  const [statusValue, setStatusValue] = useState(detail.incident.status);
  const [affectedArea, setAffectedArea] = useState(detail.incident.affected_area);
  const [featureFlagKey, setFeatureFlagKey] = useState(detail.incident.feature_flag_key || "");
  const [assignedToUserId, setAssignedToUserId] = useState(detail.incident.assigned_to_user_id?.toString() || "");
  const [customerImpactSummary, setCustomerImpactSummary] = useState(detail.incident.customer_impact_summary || "");
  const [rootCauseSummary, setRootCauseSummary] = useState(detail.incident.root_cause_summary || "");
  const [mitigatedAt, setMitigatedAt] = useState(detail.incident.mitigated_at ? detail.incident.mitigated_at.slice(0, 16) : "");
  const [saving, setSaving] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [updatingTimeline, setUpdatingTimeline] = useState(false);
  const [resolutionNote, setResolutionNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTitle(detail.incident.title);
    setSummary(detail.incident.summary);
    setSeverity(detail.incident.severity);
    setStatusValue(detail.incident.status);
    setAffectedArea(detail.incident.affected_area);
    setFeatureFlagKey(detail.incident.feature_flag_key || "");
    setAssignedToUserId(detail.incident.assigned_to_user_id?.toString() || "");
    setCustomerImpactSummary(detail.incident.customer_impact_summary || "");
    setRootCauseSummary(detail.incident.root_cause_summary || "");
    setMitigatedAt(detail.incident.mitigated_at ? detail.incident.mitigated_at.slice(0, 16) : "");
    setResolutionNote("");
    setError(null);
  }, [detail]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await onUpdate({
        title,
        summary,
        severity,
        status: statusValue,
        affected_area: affectedArea,
        feature_flag_key: featureFlagKey || null,
        assigned_to_user_id: assignedToUserId ? Number(assignedToUserId) : null,
        customer_impact_summary: customerImpactSummary || null,
        root_cause_summary: rootCauseSummary || null,
        mitigated_at: mitigatedAt ? new Date(mitigatedAt).toISOString() : null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save incident");
    } finally {
      setSaving(false);
    }
  }

  async function handleResolve() {
    setResolving(true);
    setError(null);
    try {
      await onResolve(resolutionNote);
      setResolutionNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to resolve incident");
    } finally {
      setResolving(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm text-slate-500">Incident #{detail.incident.id}</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-900">{detail.incident.title}</h2>
          </div>
          <div className="flex gap-2">
            <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-medium text-rose-700">{detail.incident.severity}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{detail.incident.status}</span>
          </div>
        </div>
        <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
          <div>
            <p className="font-medium text-slate-900">Affected area</p>
            <p>{detail.incident.affected_area}</p>
          </div>
          <div>
            <p className="font-medium text-slate-900">Assigned</p>
            <p>{detail.incident.assigned_to_user_id ? `Admin #${detail.incident.assigned_to_user_id}` : "Unassigned"}</p>
          </div>
          <div>
            <p className="font-medium text-slate-900">Started</p>
            <p>{new Date(detail.incident.started_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="font-medium text-slate-900">Resolved</p>
            <p>{detail.incident.resolved_at ? new Date(detail.incident.resolved_at).toLocaleString() : "Still open"}</p>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Incident details</h3>
        <div className="mt-4 grid gap-4">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Title</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Summary</span>
            <textarea
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              rows={4}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Severity</span>
              <select
                value={severity}
                onChange={(event) => setSeverity(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              >
                <option value="sev_1">sev_1</option>
                <option value="sev_2">sev_2</option>
                <option value="sev_3">sev_3</option>
                <option value="sev_4">sev_4</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Status</span>
              <select
                value={statusValue}
                onChange={(event) => setStatusValue(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              >
                <option value="investigating">investigating</option>
                <option value="identified">identified</option>
                <option value="monitoring">monitoring</option>
                <option value="resolved">resolved</option>
                <option value="canceled">canceled</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Affected area</span>
              <input
                value={affectedArea}
                onChange={(event) => setAffectedArea(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Assigned admin ID</span>
              <input
                type="number"
                min={1}
                value={assignedToUserId}
                onChange={(event) => setAssignedToUserId(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
                placeholder="Optional"
              />
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Feature flag key</span>
              <input
                value={featureFlagKey}
                onChange={(event) => setFeatureFlagKey(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
                placeholder="Optional"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Mitigated at</span>
              <input
                type="datetime-local"
                value={mitigatedAt}
                onChange={(event) => setMitigatedAt(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              />
            </label>
          </div>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Customer impact</span>
            <textarea
              value={customerImpactSummary}
              onChange={(event) => setCustomerImpactSummary(event.target.value)}
              rows={3}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              placeholder="What customers are seeing and how broadly it affects them"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Root cause summary</span>
            <textarea
              value={rootCauseSummary}
              onChange={(event) => setRootCauseSummary(event.target.value)}
              rows={3}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              placeholder="Leave blank until the team understands the likely cause"
            />
          </label>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={saving || !title.trim() || !summary.trim() || !affectedArea.trim()}
              className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
            >
              {saving ? "Saving..." : "Save incident"}
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Resolve incident</h3>
        <p className="mt-1 text-sm text-slate-600">Closing the incident sets its status to resolved and can append a final resolution note to the timeline.</p>
        <textarea
          value={resolutionNote}
          onChange={(event) => setResolutionNote(event.target.value)}
          rows={4}
          className="mt-4 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          placeholder="Optional resolution note"
        />
        <button
          type="button"
          onClick={() => void handleResolve()}
          disabled={resolving}
          className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 disabled:opacity-60"
        >
          {resolving ? "Resolving..." : "Resolve incident"}
        </button>
      </section>

      <IncidentUpdateForm
        submitting={updatingTimeline}
        onSubmit={async (payload) => {
          setUpdatingTimeline(true);
          setError(null);
          try {
            await onAddUpdate(payload);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Unable to add incident update");
            throw err;
          } finally {
            setUpdatingTimeline(false);
          }
        }}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Timeline</h3>
        {detail.updates.length ? (
          <div className="mt-4 space-y-4">
            {detail.updates.map((update) => (
              <div key={update.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-slate-900">{update.update_type}</p>
                  <p className="text-xs text-slate-500">
                    {new Date(update.created_at).toLocaleString()}
                    {update.author_user_id ? ` • Admin #${update.author_user_id}` : ""}
                  </p>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{update.body}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-600">No updates yet. Add one when investigation or mitigation moves forward.</p>
        )}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Related runbooks</h3>
        {relatedRunbooks.length ? (
          <div className="mt-4 space-y-3">
            {relatedRunbooks.map((runbook) => (
              <div key={runbook.id} className="rounded-2xl border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-900">{runbook.title}</p>
                    <p className="text-xs text-slate-500">
                      {runbook.key} • {runbook.area}
                    </p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${runbook.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
                    {runbook.is_active ? "active" : "inactive"}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-700">{runbook.summary}</p>
                <pre className="mt-3 overflow-x-auto rounded-2xl bg-slate-50 px-4 py-3 text-xs text-slate-700">{runbook.steps_markdown}</pre>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-600">No active runbooks are currently linked by area for this incident.</p>
        )}
      </section>
    </div>
  );
}
