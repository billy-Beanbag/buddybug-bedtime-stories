"use client";

import { useEffect, useState } from "react";

import type { BillingRecoveryCaseDetailResponse } from "@/lib/types";

const STATUS_OPTIONS = ["open", "recovered", "expired", "ignored"] as const;

function toInputDateTime(value: string | null) {
  if (!value) {
    return "";
  }
  return new Date(value).toISOString().slice(0, 16);
}

export function BillingRecoveryCaseDetail({
  detail,
  onUpdate,
  onResolve,
}: {
  detail: BillingRecoveryCaseDetailResponse;
  onUpdate: (payload: {
    recovery_status?: string;
    notes?: string | null;
    resolved_at?: string | null;
    expires_at?: string | null;
  }) => Promise<void>;
  onResolve: () => Promise<void>;
}) {
  const [recoveryStatus, setRecoveryStatus] = useState(detail.case.recovery_status);
  const [notes, setNotes] = useState(detail.case.notes || "");
  const [resolvedAt, setResolvedAt] = useState(toInputDateTime(detail.case.resolved_at));
  const [expiresAt, setExpiresAt] = useState(toInputDateTime(detail.case.expires_at));
  const [saving, setSaving] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRecoveryStatus(detail.case.recovery_status);
    setNotes(detail.case.notes || "");
    setResolvedAt(toInputDateTime(detail.case.resolved_at));
    setExpiresAt(toInputDateTime(detail.case.expires_at));
  }, [detail]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await onUpdate({
        recovery_status: recoveryStatus,
        notes: notes.trim() ? notes.trim() : null,
        resolved_at: resolvedAt ? new Date(resolvedAt).toISOString() : null,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save billing recovery case");
    } finally {
      setSaving(false);
    }
  }

  async function handleResolve() {
    setResolving(true);
    setError(null);
    try {
      await onResolve();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to resolve billing recovery case");
    } finally {
      setResolving(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{detail.case.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">{detail.case.summary}</p>
          </div>
          <div className="flex gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{detail.case.recovery_status}</span>
            <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
              {detail.case.billing_status_snapshot || "no snapshot"}
            </span>
          </div>
        </div>
        <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="text-slate-500">User</div>
            <div className="mt-1 font-medium text-slate-900">#{detail.case.user_id}</div>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="text-slate-500">Source</div>
            <div className="mt-1 font-medium text-slate-900">{detail.case.source_type}</div>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="text-slate-500">First detected</div>
            <div className="mt-1 font-medium text-slate-900">{new Date(detail.case.first_detected_at).toLocaleString()}</div>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="text-slate-500">External reference</div>
            <div className="mt-1 font-medium text-slate-900">{detail.case.external_reference || "None"}</div>
          </div>
        </div>
      </section>

      <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Recovery controls</h3>
        <div className="grid gap-3 sm:grid-cols-3">
          <select
            value={recoveryStatus}
            onChange={(event) => setRecoveryStatus(event.target.value)}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <input
            type="datetime-local"
            value={resolvedAt}
            onChange={(event) => setResolvedAt(event.target.value)}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
          <input
            type="datetime-local"
            value={expiresAt}
            onChange={(event) => setExpiresAt(event.target.value)}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        </div>
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={4}
          placeholder="Internal notes for recovery follow-up"
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <div className="grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
          >
            {saving ? "Saving..." : "Save case updates"}
          </button>
          <button
            type="button"
            onClick={() => void handleResolve()}
            disabled={resolving || detail.case.recovery_status === "recovered"}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {resolving ? "Resolving..." : "Resolve case"}
          </button>
        </div>
      </section>

      <section className="space-y-3 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Recovery events</h3>
        {detail.events.length ? (
          <div className="grid gap-3">
            {detail.events.map((event) => (
              <div key={event.id} className="rounded-2xl bg-slate-50 px-4 py-3 text-sm">
                <p className="font-medium text-slate-900">{event.event_type}</p>
                <p className="mt-2 whitespace-pre-wrap text-slate-700">{event.summary}</p>
                <p className="mt-2 text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
            No recovery events have been recorded for this case yet.
          </div>
        )}
      </section>
    </div>
  );
}
