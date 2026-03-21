"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { TranslationTaskEditor } from "@/components/admin/TranslationTaskEditor";
import { TranslationTaskTable } from "@/components/admin/TranslationTaskTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { TranslationTaskDetailResponse } from "@/lib/types";

export default function AdminTranslationsPage() {
  const { token, isEditor } = useAuth();
  const [tasks, setTasks] = useState<TranslationTaskDetailResponse[]>([]);
  const [missingItems, setMissingItems] = useState<TranslationTaskDetailResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [language, setLanguage] = useState("");
  const [statusValue, setStatusValue] = useState("");
  const [selectedItem, setSelectedItem] = useState<TranslationTaskDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadData(nextLanguage = language, nextStatus = statusValue) {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [tasksResponse, missingResponse] = await Promise.all([
        apiGet<TranslationTaskDetailResponse[]>("/admin/translations/tasks", {
          token,
          query: {
            language: nextLanguage || undefined,
            status: nextStatus || undefined,
            limit: 100,
          },
        }),
        apiGet<TranslationTaskDetailResponse[]>("/admin/translations/missing", {
          token,
          query: {
            language: nextLanguage || undefined,
            limit: 20,
          },
        }),
      ]);
      setTasks(tasksResponse);
      setMissingItems(missingResponse);
      if (selectedItem?.task) {
        const refreshed = tasksResponse.find((item) => item.task?.id === selectedItem.task?.id) || null;
        setSelectedItem(refreshed);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load translation operations");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadData();
    }
  }, [token]);

  if (!isEditor) {
    return <EmptyState title="Editor access required" description="Only editors and admins can manage translation operations." />;
  }

  if (loading) {
    return <LoadingState message="Loading translation operations..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Translation operations</h1>
        <p className="mt-2 text-sm text-slate-600">
          Track multilingual rollout work, assign internal owners, and spot books that still need translation coverage.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <input
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
            placeholder="Language filter (e.g. es)"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          />
          <select
            value={statusValue}
            onChange={(event) => setStatusValue(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="not_started">not_started</option>
            <option value="in_progress">in_progress</option>
            <option value="in_review">in_review</option>
            <option value="completed">completed</option>
            <option value="blocked">blocked</option>
          </select>
          <button
            type="button"
            onClick={() => void loadData(language, statusValue)}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Apply filters
          </button>
        </div>
      </section>

      {message ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</div>
      ) : null}
      {error ? <EmptyState title="Translation operations unavailable" description={error} /> : null}

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          {tasks.length === 0 ? (
            <EmptyState title="No translation tasks yet" description="Create the first task from a missing language opportunity or manually from the editor panel." />
          ) : (
            <TranslationTaskTable
              items={tasks}
              selectedTaskId={selectedItem?.task?.id || null}
              onSelect={(item) => setSelectedItem(item)}
            />
          )}

          <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Missing translation opportunities</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Published books that still lack full translation coverage for the selected language or supported locales.
                </p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">{missingItems.length} items</span>
            </div>
            <div className="mt-4 space-y-3">
              {missingItems.length ? (
                missingItems.map((item) => (
                  <div key={`${item.book_id}-${item.target_language}`} className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-slate-900">
                          {item.book_title} • {item.target_language.toUpperCase()}
                        </p>
                        <p className="mt-1 text-sm text-slate-600">
                          {item.translated_page_count}/{item.total_page_count} pages translated •{" "}
                          {item.has_book_translation ? "metadata exists" : "metadata missing"}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setSelectedItem(item)}
                        className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900"
                      >
                        {item.task ? "Open task" : "Create task"}
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-600">No missing translation opportunities match the current filters.</p>
              )}
            </div>
          </section>
        </div>

        <TranslationTaskEditor
          item={selectedItem}
          saving={saving}
          onCreate={async (payload) => {
            if (!token) {
              return;
            }
            setSaving(true);
            setError(null);
            setMessage(null);
            try {
              const created = await apiPost<TranslationTaskDetailResponse>("/admin/translations/tasks", payload, { token });
              setSelectedItem(created);
              setMessage(`Created translation task for ${created.book_title} (${created.target_language.toUpperCase()}).`);
              await loadData();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Unable to create translation task");
            } finally {
              setSaving(false);
            }
          }}
          onUpdate={async (taskId, payload) => {
            if (!token) {
              return;
            }
            setSaving(true);
            setError(null);
            setMessage(null);
            try {
              const updated = await apiPatch<TranslationTaskDetailResponse>(`/admin/translations/tasks/${taskId}`, payload, {
                token,
              });
              setSelectedItem(updated);
              setMessage(`Updated translation task for ${updated.book_title} (${updated.target_language.toUpperCase()}).`);
              await loadData();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Unable to update translation task");
            } finally {
              setSaving(false);
            }
          }}
        />
      </div>
    </div>
  );
}
