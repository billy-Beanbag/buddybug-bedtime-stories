"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { PublicStatusComponentTable } from "@/components/admin/PublicStatusComponentTable";
import { PublicStatusNoticeEditor, type PublicStatusNoticeFormValue } from "@/components/admin/PublicStatusNoticeEditor";
import { PublicStatusNoticeTable } from "@/components/admin/PublicStatusNoticeTable";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import type { PublicStatusComponentRead, PublicStatusNoticeRead } from "@/lib/types";

function toPayload(value: PublicStatusNoticeFormValue) {
  return {
    title: value.title,
    summary: value.summary,
    notice_type: value.notice_type,
    public_status: value.public_status,
    component_key: value.component_key || null,
    linked_incident_id: value.linked_incident_id ? Number(value.linked_incident_id) : null,
    starts_at: value.starts_at ? new Date(value.starts_at).toISOString() : null,
    ends_at: value.ends_at ? new Date(value.ends_at).toISOString() : null,
    is_active: value.is_active,
    is_public: value.is_public,
  };
}

export default function AdminPublicStatusPage() {
  const { token, isAdmin } = useAuth();
  const [components, setComponents] = useState<PublicStatusComponentRead[]>([]);
  const [notices, setNotices] = useState<PublicStatusNoticeRead[]>([]);
  const [selectedNotice, setSelectedNotice] = useState<PublicStatusNoticeRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [updatingComponentId, setUpdatingComponentId] = useState<number | null>(null);
  const [deletingNoticeId, setDeletingNoticeId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadStatusAdmin() {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const [componentResponse, noticeResponse] = await Promise.all([
        apiGet<PublicStatusComponentRead[]>("/admin/status/components", { token }),
        apiGet<PublicStatusNoticeRead[]>("/admin/status/notices", { token }),
      ]);
      setComponents(componentResponse);
      setNotices(noticeResponse);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load public status admin tools");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadStatusAdmin();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage public status." />;
  }

  if (loading) {
    return <LoadingState message="Loading public status tools..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Public status</h1>
        <p className="mt-2 text-sm text-slate-600">
          Publish customer-safe service health updates without exposing internal-only incident detail or operational notes.
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
          {components.length ? (
            <PublicStatusComponentTable
              components={components}
              updatingComponentId={updatingComponentId}
              onUpdate={async (component, patch) => {
                if (!token) {
                  return;
                }
                setUpdatingComponentId(component.id);
                setStatusMessage(null);
                setErrorMessage(null);
                try {
                  await apiPatch(`/admin/status/components/${component.id}`, patch, { token });
                  setStatusMessage(`Updated component "${component.name}".`);
                  await loadStatusAdmin();
                } catch (err) {
                  setErrorMessage(err instanceof Error ? err.message : "Unable to update public status component");
                } finally {
                  setUpdatingComponentId(null);
                }
              }}
            />
          ) : (
            <EmptyState title="No public status components yet" description="Run migrations and startup seeding to create the default public status components." />
          )}

          {notices.length ? (
            <PublicStatusNoticeTable
              notices={notices}
              deletingNoticeId={deletingNoticeId}
              onEdit={(notice) => setSelectedNotice(notice)}
              onDelete={async (notice) => {
                if (!token) {
                  return;
                }
                setDeletingNoticeId(notice.id);
                setStatusMessage(null);
                setErrorMessage(null);
                try {
                  await apiDelete(`/admin/status/notices/${notice.id}`, { token });
                  if (selectedNotice?.id === notice.id) {
                    setSelectedNotice(null);
                  }
                  setStatusMessage(`Deleted public notice "${notice.title}".`);
                  await loadStatusAdmin();
                } catch (err) {
                  setErrorMessage(err instanceof Error ? err.message : "Unable to delete public notice");
                } finally {
                  setDeletingNoticeId(null);
                }
              }}
            />
          ) : (
            <EmptyState title="No public notices yet" description="Create the first customer-facing incident or maintenance notice when needed." />
          )}
        </div>

        <PublicStatusNoticeEditor
          components={components}
          notice={selectedNotice}
          submitting={saving}
          onSubmit={async (value) => {
            if (!token) {
              return;
            }
            setSaving(true);
            setStatusMessage(null);
            setErrorMessage(null);
            try {
              if (selectedNotice) {
                await apiPatch<PublicStatusNoticeRead>(`/admin/status/notices/${selectedNotice.id}`, toPayload(value), { token });
                setStatusMessage(`Updated public notice "${value.title}".`);
              } else {
                await apiPost<PublicStatusNoticeRead>("/admin/status/notices", toPayload(value), { token });
                setStatusMessage(`Created public notice "${value.title}".`);
              }
              setSelectedNotice(null);
              await loadStatusAdmin();
            } catch (err) {
              setErrorMessage(err instanceof Error ? err.message : "Unable to save public notice");
            } finally {
              setSaving(false);
            }
          }}
          onCancel={selectedNotice ? () => setSelectedNotice(null) : undefined}
        />
      </div>
    </div>
  );
}
