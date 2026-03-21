"use client";

import { useEffect, useState } from "react";

import { ChangelogEditor, type ChangelogFormValue } from "@/components/admin/ChangelogEditor";
import { ChangelogTable } from "@/components/admin/ChangelogTable";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { ChangelogEntryRead } from "@/lib/types";

function toPayload(form: ChangelogFormValue) {
  return {
    ...form,
    details_markdown: form.details_markdown || null,
    area_tags: form.area_tags || null,
    feature_flag_keys: form.feature_flag_keys || null,
  };
}

export default function AdminChangelogPage() {
  const { token, isEditor } = useAuth();
  const [entries, setEntries] = useState<ChangelogEntryRead[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<ChangelogEntryRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishingId, setPublishingId] = useState<number | null>(null);
  const [archivingId, setArchivingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [audienceFilter, setAudienceFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  async function loadEntries(nextAudience = audienceFilter, nextStatus = statusFilter) {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<ChangelogEntryRead[]>("/admin/changelog", {
        token,
        query: {
          audience: nextAudience || undefined,
          status: nextStatus || undefined,
          limit: 100,
        },
      });
      setEntries(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load changelog");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadEntries();
    }
  }, [token]);

  if (!isEditor) {
    return <EmptyState title="Editor access required" description="Only editors and admins can manage the changelog." />;
  }

  if (loading) {
    return <LoadingState message="Loading changelog..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Changelog and release notes</h1>
        <p className="mt-2 text-sm text-slate-600">
          Keep internal release notes organized now, and stage user-facing "what’s new" updates when launch messaging is ready.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={audienceFilter}
            onChange={(event) => setAudienceFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All audiences</option>
            <option value="internal">internal</option>
            <option value="user_facing">user_facing</option>
          </select>
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="draft">draft</option>
            <option value="published">published</option>
            <option value="archived">archived</option>
          </select>
          <button
            type="button"
            onClick={() => void loadEntries(audienceFilter, statusFilter)}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
          >
            Apply filters
          </button>
        </div>
      </section>

      <ChangelogEditor
        entry={selectedEntry}
        submitting={saving}
        onSubmit={async (form) => {
          if (!token) {
            return;
          }
          setSaving(true);
          setError(null);
          setStatusMessage(null);
          try {
            if (selectedEntry) {
              await apiPatch(`/admin/changelog/${selectedEntry.id}`, toPayload(form), { token });
              setStatusMessage(`Updated changelog entry "${form.title}".`);
            } else {
              await apiPost("/admin/changelog", toPayload(form), { token });
              setStatusMessage(`Created changelog entry "${form.title}".`);
            }
            setSelectedEntry(null);
            await loadEntries();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Unable to save changelog entry");
          } finally {
            setSaving(false);
          }
        }}
        onCancel={selectedEntry ? () => setSelectedEntry(null) : undefined}
      />

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {error ? <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}

      {entries.length ? (
        <ChangelogTable
          entries={entries}
          publishingId={publishingId}
          archivingId={archivingId}
          onEdit={(entry) => setSelectedEntry(entry)}
          onPublish={async (entry) => {
            if (!token) {
              return;
            }
            setPublishingId(entry.id);
            setError(null);
            setStatusMessage(null);
            try {
              await apiPost(`/admin/changelog/${entry.id}/publish`, undefined, { token });
              setStatusMessage(`Published "${entry.title}".`);
              await loadEntries();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Unable to publish changelog entry");
            } finally {
              setPublishingId(null);
            }
          }}
          onArchive={async (entry) => {
            if (!token) {
              return;
            }
            setArchivingId(entry.id);
            setError(null);
            setStatusMessage(null);
            try {
              await apiPost(`/admin/changelog/${entry.id}/archive`, undefined, { token });
              if (selectedEntry?.id === entry.id) {
                setSelectedEntry(null);
              }
              setStatusMessage(`Archived "${entry.title}".`);
              await loadEntries();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Unable to archive changelog entry");
            } finally {
              setArchivingId(null);
            }
          }}
        />
      ) : (
        <EmptyState title="No changelog entries yet" description="Create the first release note entry to start documenting Buddybug changes." />
      )}
    </div>
  );
}
