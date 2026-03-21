"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ClassroomSetEditor, type ClassroomSetFormValue } from "@/components/educator/ClassroomSetEditor";
import { ClassroomSetList } from "@/components/educator/ClassroomSetList";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { ClassroomSetRead } from "@/lib/types";

function toPayload(form: ClassroomSetFormValue) {
  return {
    title: form.title,
    description: form.description || null,
    age_band: form.age_band || null,
    language: form.language || null,
    is_active: form.is_active,
  };
}

export default function EducatorPage() {
  const { token, isEducator, isLoading } = useAuth();
  const [sets, setSets] = useState<ClassroomSetRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadSets() {
    if (!token) {
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const response = await apiGet<ClassroomSetRead[]>("/educator/classroom-sets", { token });
      setSets(response);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Unable to load classroom sets");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token && isEducator) {
      void loadSets();
    } else if (!isLoading) {
      setLoading(false);
    }
  }, [isEducator, isLoading, token]);

  if (isLoading || loading) {
    return <LoadingState message="Loading educator workspace..." />;
  }

  if (!isEducator) {
    return (
      <EmptyState
        title="Educator access required"
        description="This workspace is reserved for trusted educator or admin accounts."
      />
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Educator workspace</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Build teacher-friendly classroom reading sets without mixing them into the family bedtime flow.
        </p>
      </section>

      <ClassroomSetEditor
        submitting={saving}
        submitLabel="Create classroom set"
        onSubmit={async (form) => {
          if (!token) {
            return;
          }
          setSaving(true);
          setStatusMessage(null);
          try {
            await apiPost<ClassroomSetRead>("/educator/classroom-sets", toPayload(form), { token });
            await loadSets();
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to create classroom set");
          } finally {
            setSaving(false);
          }
        }}
      />

      {statusMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{statusMessage}</div>
      ) : null}

      {sets.length ? (
        <ClassroomSetList sets={sets} />
      ) : (
        <EmptyState
          title="No classroom sets yet"
          description="Create your first educator-managed reading set to start organizing books for classroom use."
        />
      )}
    </div>
  );
}
