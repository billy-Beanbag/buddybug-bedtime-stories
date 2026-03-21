"use client";

import { useEffect, useState } from "react";

import type { ModerationCaseDetailResponse } from "@/lib/types";

export function ModerationCaseDetail({
  detail,
  onUpdate,
  onResolve,
  onDismiss,
}: {
  detail: ModerationCaseDetailResponse;
  onUpdate: (payload: Record<string, unknown>) => Promise<void>;
  onResolve: () => Promise<void>;
  onDismiss: () => Promise<void>;
}) {
  const [severity, setSeverity] = useState(detail.case.severity);
  const [statusValue, setStatusValue] = useState(detail.case.status);
  const [assignedToUserId, setAssignedToUserId] = useState(detail.case.assigned_to_user_id?.toString() || "");
  const [summary, setSummary] = useState(detail.case.summary);
  const [notes, setNotes] = useState(detail.case.notes || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSeverity(detail.case.severity);
    setStatusValue(detail.case.status);
    setAssignedToUserId(detail.case.assigned_to_user_id?.toString() || "");
    setSummary(detail.case.summary);
    setNotes(detail.case.notes || "");
  }, [detail]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await onUpdate({
        severity,
        status: statusValue,
        assigned_to_user_id: assignedToUserId ? Number(assignedToUserId) : null,
        summary,
        notes: notes || null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update moderation case");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm text-slate-500">
              {detail.case.case_type} • case #{detail.case.id}
            </p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-900">{detail.case.summary}</h2>
          </div>
          <div className="flex gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{detail.case.status}</span>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">{detail.case.severity}</span>
          </div>
        </div>
        <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
          <div>
            <p className="font-medium text-slate-900">Target</p>
            <p>{detail.target_summary || `${detail.case.target_type} ${detail.case.target_id ? `#${detail.case.target_id}` : ""}`}</p>
          </div>
          <div>
            <p className="font-medium text-slate-900">Source</p>
            <p>{detail.source_summary || `${detail.case.source_type} ${detail.case.source_id ? `#${detail.case.source_id}` : ""}`}</p>
          </div>
          <div>
            <p className="font-medium text-slate-900">Created</p>
            <p>{new Date(detail.case.created_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="font-medium text-slate-900">Resolved</p>
            <p>{detail.case.resolved_at ? new Date(detail.case.resolved_at).toLocaleString() : "Still open"}</p>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Triage</h3>
        <div className="mt-4 grid gap-4">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Summary</span>
            <input
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Severity</span>
              <select
                value={severity}
                onChange={(event) => setSeverity(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="critical">critical</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Status</span>
              <select
                value={statusValue}
                onChange={(event) => setStatusValue(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              >
                <option value="open">open</option>
                <option value="triaging">triaging</option>
                <option value="resolved">resolved</option>
                <option value="dismissed">dismissed</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Assigned user ID</span>
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
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Notes</span>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={6}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              placeholder="Internal moderation context, decision notes, or next steps"
            />
          </label>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={saving || !summary.trim()}
              className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
            >
              {saving ? "Saving..." : "Save case"}
            </button>
            <button
              type="button"
              onClick={() => void onResolve()}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
            >
              Resolve case
            </button>
            <button
              type="button"
              onClick={() => void onDismiss()}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
            >
              Dismiss case
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
