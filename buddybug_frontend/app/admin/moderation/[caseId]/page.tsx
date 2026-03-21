"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ModerationCaseDetail } from "@/components/admin/ModerationCaseDetail";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { ModerationCaseDetailResponse } from "@/lib/types";

export default function AdminModerationCaseDetailPage() {
  const params = useParams<{ caseId: string }>();
  const caseId = Number(params.caseId);
  const { token, isEditor } = useAuth();
  const [detail, setDetail] = useState<ModerationCaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    if (!token || !caseId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<ModerationCaseDetailResponse>(`/admin/moderation/cases/${caseId}`, { token });
      setDetail(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load moderation case");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadDetail();
    }
  }, [caseId, token]);

  if (!isEditor) {
    return <EmptyState title="Editor access required" description="Only editors and admins can manage moderation cases." />;
  }

  if (loading) {
    return <LoadingState message="Loading moderation case..." />;
  }

  if (error || !detail) {
    return <EmptyState title="Unable to load moderation case" description={error || "Moderation case not found."} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">Moderation case</p>
          <h1 className="text-2xl font-semibold text-slate-900">#{detail.case.id}</h1>
        </div>
        <Link
          href="/admin/moderation"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Back to queue
        </Link>
      </div>

      <ModerationCaseDetail
        detail={detail}
        onUpdate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPatch(`/admin/moderation/cases/${caseId}`, payload, { token });
          await loadDetail();
        }}
        onResolve={async () => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/moderation/cases/${caseId}/resolve`, undefined, { token });
          await loadDetail();
        }}
        onDismiss={async () => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/moderation/cases/${caseId}/dismiss`, undefined, { token });
          await loadDetail();
        }}
      />
    </div>
  );
}
