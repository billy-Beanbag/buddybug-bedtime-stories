"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { RunbookEditor, type RunbookFormValue } from "@/components/admin/RunbookEditor";
import { RunbookTable } from "@/components/admin/RunbookTable";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { RunbookEntryRead } from "@/lib/types";

export default function AdminRunbooksPage() {
  const { token, isAdmin } = useAuth();
  const [runbooks, setRunbooks] = useState<RunbookEntryRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [selectedRunbook, setSelectedRunbook] = useState<RunbookEntryRead | null>(null);
  const [areaFilter, setAreaFilter] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadRunbooks(nextArea = areaFilter, nextShowInactive = showInactive) {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await apiGet<RunbookEntryRead[]>("/admin/runbooks", {
        token,
        query: {
          area: nextArea || undefined,
          is_active: nextShowInactive ? undefined : true,
          limit: 100,
        },
      });
      setRunbooks(response);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load runbooks");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadRunbooks();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage runbooks." />;
  }

  if (loading) {
    return <LoadingState message="Loading runbooks..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Ops runbooks</h1>
        <p className="mt-2 text-sm text-slate-600">
          Keep lightweight recovery guides for recurring issues so incident response stays consistent across shifts and follow-up work.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <input
            value={areaFilter}
            onChange={(event) => setAreaFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="Filter by area"
          />
          <label className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
            <input type="checkbox" checked={showInactive} onChange={(event) => setShowInactive(event.target.checked)} />
            Include inactive
          </label>
          <button
            type="button"
            onClick={() => void loadRunbooks(areaFilter, showInactive)}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
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

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div>
          {runbooks.length ? (
            <RunbookTable
              runbooks={runbooks}
              savingId={savingId}
              onEdit={(runbook) => {
                setSelectedRunbook(runbook);
                setStatusMessage(null);
                setErrorMessage(null);
              }}
              onDeactivate={async (runbook) => {
                if (!token) {
                  return;
                }
                setSavingId(runbook.id);
                setStatusMessage(null);
                setErrorMessage(null);
                try {
                  await apiDelete(`/admin/runbooks/${runbook.id}`, { token });
                  setStatusMessage(`Deactivated runbook "${runbook.title}".`);
                  await loadRunbooks();
                  if (selectedRunbook?.id === runbook.id) {
                    setSelectedRunbook(null);
                  }
                } catch (err) {
                  setErrorMessage(err instanceof Error ? err.message : "Unable to deactivate runbook");
                } finally {
                  setSavingId(null);
                }
              }}
            />
          ) : (
            <EmptyState title="No runbooks match these filters" description="Create one for a common operational recovery path." />
          )}
        </div>

        <RunbookEditor
          runbook={selectedRunbook}
          submitting={submitting}
          onSubmit={async (value: RunbookFormValue) => {
            if (!token) {
              return;
            }
            setSubmitting(true);
            setStatusMessage(null);
            setErrorMessage(null);
            try {
              if (selectedRunbook) {
                await apiPatch(`/admin/runbooks/${selectedRunbook.id}`, value, { token });
                setStatusMessage(`Updated runbook "${value.title}".`);
              } else {
                await apiPost("/admin/runbooks", value, { token });
                setStatusMessage(`Created runbook "${value.title}".`);
              }
              setSelectedRunbook(null);
              await loadRunbooks();
            } catch (err) {
              setErrorMessage(err instanceof Error ? err.message : "Unable to save runbook");
            } finally {
              setSubmitting(false);
            }
          }}
          onCancel={() => setSelectedRunbook(null)}
        />
      </div>
    </div>
  );
}
