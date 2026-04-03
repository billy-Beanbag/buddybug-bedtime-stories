"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON, ADMIN_SECONDARY_BUTTON } from "@/lib/admin-styles";
import type { StorySuggestionAdminListResponse, StorySuggestionAdminRead } from "@/lib/types";

const STATUS_OPTIONS = ["submitted", "in_review", "approved", "archived"] as const;

function formatStatusLabel(status: string) {
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function AdminStorySuggestionsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<StorySuggestionAdminRead[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);

  async function loadSuggestions() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<StorySuggestionAdminListResponse>("/admin/story-suggestions", {
        token,
        query: { status: statusFilter || undefined },
      });
      setItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load story suggestions");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSuggestions();
  }, [token, statusFilter]);

  async function handleQuickUpdate(
    suggestionId: number,
    payload: { status?: string; approved_as_reference?: boolean; editorial_notes?: string | null },
  ) {
    if (!token) {
      return;
    }
    setSavingId(suggestionId);
    setError(null);
    setMessage(null);
    try {
      const updated = await apiPatch<StorySuggestionAdminRead>(`/admin/story-suggestions/${suggestionId}`, payload, { token });
      setItems((current) => current.map((item) => (item.id === suggestionId ? updated : item)));
      setMessage(`Suggestion ${suggestionId} updated.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update story suggestion");
    } finally {
      setSavingId(null);
    }
  }

  async function handleDelete(suggestion: StorySuggestionAdminRead) {
    if (!token) {
      return;
    }
    const label = suggestion.title || `Suggestion ${suggestion.id}`;
    const confirmed = window.confirm(`Delete "${label}" permanently? This cannot be undone.`);
    if (!confirmed) {
      return;
    }
    setSavingId(suggestion.id);
    setError(null);
    setMessage(null);
    try {
      await apiDelete(`/admin/story-suggestions/${suggestion.id}`, { token });
      setItems((current) => current.filter((item) => item.id !== suggestion.id));
      setMessage(`Deleted ${label}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete story suggestion");
    } finally {
      setSavingId(null);
    }
  }

  async function handlePromoteToIdea(suggestion: StorySuggestionAdminRead) {
    if (!token) {
      return;
    }
    setSavingId(suggestion.id);
    setError(null);
    setMessage(null);
    try {
      const updated = await apiPost<StorySuggestionAdminRead>(
        `/admin/story-suggestions/${suggestion.id}/promote-to-idea`,
        {},
        { token },
      );
      setItems((current) => current.map((item) => (item.id === suggestion.id ? updated : item)));
      setMessage(
        updated.promoted_story_idea_id
          ? `Suggestion ${suggestion.id} promoted to idea ${updated.promoted_story_idea_id}.`
          : `Suggestion ${suggestion.id} was already promoted.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to promote story suggestion");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Story suggestions</h2>
          <p className="mt-1 text-sm text-slate-600">
            Review parent-submitted briefs, approve reusable references, or promote a suggestion directly into the ideas
            queue.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {formatStatusLabel(status)}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void loadSuggestions()}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Refresh
          </button>
        </div>
      </div>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {loading ? <LoadingState message="Loading suggestion queue..." /> : null}

      {!loading && !items.length ? (
        <EmptyState
          title="No story suggestions found"
          description="Parent-submitted story ideas will appear here once families start sending them in."
        />
      ) : null}

      {!loading ? (
        <div className="space-y-3">
          {items.map((item) => (
            <article key={item.id} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700">
                      {formatStatusLabel(item.status)}
                    </span>
                    {item.approved_as_reference ? (
                      <span className="rounded-full bg-emerald-100 px-3 py-2 text-sm font-medium text-emerald-800">
                        Reusable reference
                      </span>
                    ) : null}
                    {item.promoted_story_idea_id ? (
                      <span className="rounded-full bg-indigo-100 px-3 py-2 text-sm font-medium text-indigo-800">
                        Promoted to idea #{item.promoted_story_idea_id}
                      </span>
                    ) : null}
                    {!item.allow_reference_use ? (
                      <span className="rounded-full bg-amber-100 px-3 py-2 text-sm font-medium text-amber-800">
                        No reuse permission
                      </span>
                    ) : null}
                  </div>
                  <h3 className="mt-3 text-base font-semibold text-slate-900">{item.title || "Untitled suggestion"}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{item.brief}</p>
                  <div className="mt-3 text-sm text-slate-500">
                    {(item.user_display_name || item.user_email || `User ${item.user_id}`) + " • "}
                    {(item.child_profile_name || "General family idea") + " • "}
                    {item.age_band} • {item.language.toUpperCase()}
                  </div>
                  {item.desired_outcome ? (
                    <p className="mt-3 text-sm text-slate-600">
                      <span className="font-medium text-slate-900">Goal:</span> {item.desired_outcome}
                    </p>
                  ) : null}
                  {item.inspiration_notes ? (
                    <p className="mt-2 text-sm text-slate-600">
                      <span className="font-medium text-slate-900">Include:</span> {item.inspiration_notes}
                    </p>
                  ) : null}
                  {item.avoid_notes ? (
                    <p className="mt-2 text-sm text-slate-600">
                      <span className="font-medium text-slate-900">Avoid:</span> {item.avoid_notes}
                    </p>
                  ) : null}
                  <label className="mt-4 block text-sm text-slate-700">
                    <span className="mb-1 block font-medium text-slate-900">Editorial notes</span>
                    <textarea
                      defaultValue={item.editorial_notes || ""}
                      rows={3}
                      onBlur={(event) => {
                        const nextValue = event.target.value.trim();
                        if ((item.editorial_notes || "") === nextValue) {
                          return;
                        }
                        void handleQuickUpdate(item.id, { editorial_notes: nextValue || null });
                      }}
                      className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                    />
                  </label>
                  {item.promoted_story_idea_id ? (
                    <p className="mt-3 text-sm text-slate-600">
                      <span className="font-medium text-slate-900">Ideas queue:</span>{" "}
                      {item.promoted_story_idea_title || `Story idea ${item.promoted_story_idea_id}`} is now available in{" "}
                      <Link href="/admin/ideas" className="text-indigo-700 underline-offset-2 hover:underline">
                        Admin Ideas
                      </Link>
                      .
                    </p>
                  ) : null}
                </div>
                <div className="flex w-full flex-col gap-2 lg:w-[220px]">
                  <button
                    type="button"
                    disabled={savingId === item.id}
                    onClick={() => void handleQuickUpdate(item.id, { status: "in_review" })}
                    className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_SECONDARY_BUTTON}`}
                  >
                    Mark in review
                  </button>
                  <button
                    type="button"
                    disabled={savingId === item.id}
                    onClick={() => void handleQuickUpdate(item.id, { status: "approved" })}
                    className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={savingId === item.id || !item.allow_reference_use}
                    onClick={() => void handleQuickUpdate(item.id, { approved_as_reference: !item.approved_as_reference })}
                    className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_SECONDARY_BUTTON}`}
                  >
                    {item.approved_as_reference ? "Remove reference flag" : "Approve as reference"}
                  </button>
                  <button
                    type="button"
                    disabled={savingId === item.id}
                    onClick={() => void handlePromoteToIdea(item)}
                    className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON} disabled:opacity-60`}
                  >
                    {item.promoted_story_idea_id ? "Refresh promoted idea" : "Promote to idea"}
                  </button>
                  <button
                    type="button"
                    disabled={savingId === item.id}
                    onClick={() => void handleQuickUpdate(item.id, { status: "archived" })}
                    className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_SECONDARY_BUTTON}`}
                  >
                    Archive
                  </button>
                  <button
                    type="button"
                    disabled={savingId === item.id}
                    onClick={() => void handleDelete(item)}
                    className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800 transition hover:bg-rose-100 disabled:opacity-60"
                  >
                    Delete permanently
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
