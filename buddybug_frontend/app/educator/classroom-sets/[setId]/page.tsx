"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ClassroomSetEditor, type ClassroomSetFormValue } from "@/components/educator/ClassroomSetEditor";
import { ClassroomSetItemsEditor } from "@/components/educator/ClassroomSetItemsEditor";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPatch } from "@/lib/api";
import type { ClassroomSetDetailResponse } from "@/lib/types";

function toPayload(form: ClassroomSetFormValue) {
  return {
    title: form.title,
    description: form.description || null,
    age_band: form.age_band || null,
    language: form.language || null,
    is_active: form.is_active,
  };
}

export default function EducatorClassroomSetDetailPage() {
  const params = useParams<{ setId: string }>();
  const setId = Number(params.setId);
  const { token, isEducator, isLoading } = useAuth();
  const [detail, setDetail] = useState<ClassroomSetDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadDetail() {
    if (!token || !setId) {
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const response = await apiGet<ClassroomSetDetailResponse>(`/educator/classroom-sets/${setId}`, { token });
      setDetail(response);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Unable to load classroom set");
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token && isEducator && setId) {
      void loadDetail();
    } else if (!isLoading) {
      setLoading(false);
    }
  }, [isEducator, isLoading, setId, token]);

  if (isLoading || loading) {
    return <LoadingState message="Loading classroom set..." />;
  }

  if (!isEducator) {
    return (
      <EmptyState
        title="Educator access required"
        description="Only educator or admin users can manage classroom reading sets."
      />
    );
  }

  if (!detail) {
    return <EmptyState title="Classroom set unavailable" description={statusMessage || "This classroom set could not be loaded."} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Educator</p>
          <h1 className="text-2xl font-semibold text-slate-900">{detail.classroom_set.title}</h1>
        </div>
        <Link
          href="/educator"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Back to workspace
        </Link>
      </div>

      {statusMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{statusMessage}</div>
      ) : null}

      <ClassroomSetEditor
        classroomSet={detail.classroom_set}
        submitting={saving}
        submitLabel="Save classroom set"
        onSubmit={async (form) => {
          if (!token) {
            return;
          }
          setSaving(true);
          setStatusMessage(null);
          try {
            await apiPatch(`/educator/classroom-sets/${setId}`, toPayload(form), { token });
            await loadDetail();
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to update classroom set");
          } finally {
            setSaving(false);
          }
        }}
      />

      <div className="flex justify-end">
        <button
          type="button"
          disabled={deleting}
          onClick={async () => {
            if (!token) {
              return;
            }
            setDeleting(true);
            setStatusMessage(null);
            try {
              await apiDelete(`/educator/classroom-sets/${setId}`, { token });
              window.location.assign("/educator");
            } catch (err) {
              setStatusMessage(err instanceof Error ? err.message : "Unable to delete classroom set");
              setDeleting(false);
            }
          }}
          className="rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm font-medium text-rose-700 disabled:opacity-60"
        >
          {deleting ? "Deleting..." : "Delete classroom set"}
        </button>
      </div>

      <ClassroomSetItemsEditor classroomSet={detail.classroom_set} detail={detail} token={token!} onChanged={loadDetail} />
    </div>
  );
}
