"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ModerationCaseTable } from "@/components/admin/ModerationCaseTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { ModerationCaseRead } from "@/lib/types";

export default function AdminModerationPage() {
  const { token, isEditor } = useAuth();
  const [cases, setCases] = useState<ModerationCaseRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [statusValue, setStatusValue] = useState("");
  const [severity, setSeverity] = useState("");
  const [caseType, setCaseType] = useState("");
  const [summary, setSummary] = useState("");
  const [notes, setNotes] = useState("");
  const [manualSeverity, setManualSeverity] = useState("medium");
  const [targetType, setTargetType] = useState("book");
  const [targetId, setTargetId] = useState("");

  async function loadCases(nextStatus = statusValue, nextSeverity = severity, nextCaseType = caseType) {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<ModerationCaseRead[]>("/admin/moderation/cases", {
        token,
        query: {
          status: nextStatus || undefined,
          severity: nextSeverity || undefined,
          case_type: nextCaseType || undefined,
          limit: 100,
        },
      });
      setCases(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load moderation queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadCases();
    }
  }, [token]);

  if (!isEditor) {
    return <EmptyState title="Editor access required" description="Only editors and admins can manage moderation cases." />;
  }

  if (loading) {
    return <LoadingState message="Loading moderation queue..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Moderation queue</h1>
        <p className="mt-2 text-sm text-slate-600">
          Centralize parent content concerns and severe quality failures into one internal review queue.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={statusValue}
            onChange={(event) => setStatusValue(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="open">open</option>
            <option value="triaging">triaging</option>
            <option value="resolved">resolved</option>
            <option value="dismissed">dismissed</option>
          </select>
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All severities</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="critical">critical</option>
          </select>
          <select
            value={caseType}
            onChange={(event) => setCaseType(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All case types</option>
            <option value="content_concern">content_concern</option>
            <option value="quality_failure">quality_failure</option>
            <option value="manual_escalation">manual_escalation</option>
            <option value="parental_report">parental_report</option>
          </select>
          <button
            type="button"
            onClick={() => void loadCases(statusValue, severity, caseType)}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
          >
            Apply filters
          </button>
        </div>
      </section>

      {message ? <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <EmptyState title="Moderation queue unavailable" description={error} /> : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div>
          {cases.length ? (
            <ModerationCaseTable cases={cases} />
          ) : (
            <EmptyState title="No moderation cases match these filters" description="Try a different filter or wait for the next escalation." />
          )}
        </div>

        <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Manual escalation</h2>
          <p className="mt-1 text-sm text-slate-600">Create a moderation case directly when staff need to escalate something outside the automated hooks.</p>
          <div className="mt-4 grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Target type</span>
                <select
                  value={targetType}
                  onChange={(event) => setTargetType(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                >
                  <option value="book">book</option>
                  <option value="story_draft">story_draft</option>
                  <option value="story_page">story_page</option>
                  <option value="support_ticket">support_ticket</option>
                  <option value="quality_check">quality_check</option>
                  <option value="unknown">unknown</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Target ID</span>
                <input
                  type="number"
                  min={1}
                  value={targetId}
                  onChange={(event) => setTargetId(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                  placeholder="Optional"
                />
              </label>
            </div>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Summary</span>
              <input
                value={summary}
                onChange={(event) => setSummary(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                placeholder="Why this needs moderation review"
              />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Severity</span>
                <select
                  value={manualSeverity}
                  onChange={(event) => setManualSeverity(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                  <option value="critical">critical</option>
                </select>
              </label>
            </div>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Notes</span>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={5}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                placeholder="Internal moderation context"
              />
            </label>
            <button
              type="button"
              disabled={saving || !summary.trim()}
              onClick={() => {
                if (!token) {
                  return;
                }
                setSaving(true);
                setError(null);
                setMessage(null);
                void apiPost<ModerationCaseRead>(
                  "/admin/moderation/cases",
                  {
                    case_type: "manual_escalation",
                    target_type: targetType,
                    target_id: targetId ? Number(targetId) : null,
                    source_type: "manual",
                    severity: manualSeverity,
                    status: "open",
                    summary,
                    notes: notes || null,
                  },
                  { token },
                )
                  .then(async (created) => {
                    setSummary("");
                    setNotes("");
                    setTargetId("");
                    setMessage(`Created moderation case #${created.id}.`);
                    await loadCases();
                  })
                  .catch((err: unknown) => {
                    setError(err instanceof Error ? err.message : "Unable to create moderation case");
                  })
                  .finally(() => {
                    setSaving(false);
                  });
              }}
              className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
            >
              {saving ? "Creating..." : "Create moderation case"}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
