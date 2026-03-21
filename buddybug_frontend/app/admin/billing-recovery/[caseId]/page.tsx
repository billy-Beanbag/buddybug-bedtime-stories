"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { BillingRecoveryCaseDetail } from "@/components/admin/BillingRecoveryCaseDetail";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { BillingRecoveryCaseDetailResponse } from "@/lib/types";

export default function AdminBillingRecoveryDetailPage() {
  const params = useParams<{ caseId: string }>();
  const caseId = Number(params.caseId);
  const { token, isAdmin } = useAuth();
  const [detail, setDetail] = useState<BillingRecoveryCaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    if (!token || !caseId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<BillingRecoveryCaseDetailResponse>(`/admin/billing-recovery/cases/${caseId}`, { token });
      setDetail(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load billing recovery case");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadDetail();
    }
  }, [caseId, token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can review billing recovery cases." />;
  }

  if (loading) {
    return <LoadingState message="Loading billing recovery case..." />;
  }

  if (error || !detail) {
    return <EmptyState title="Unable to load billing recovery case" description={error || "Case not found."} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">Billing recovery console</p>
          <h1 className="text-2xl font-semibold text-slate-900">Case #{detail.case.id}</h1>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            href={`/admin/lifecycle/${detail.case.user_id}`}
            className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900"
          >
            User lifecycle
          </Link>
          <Link
            href="/admin/billing-recovery"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
          >
            Back to recovery queue
          </Link>
        </div>
      </div>

      <BillingRecoveryCaseDetail
        detail={detail}
        onUpdate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPatch(`/admin/billing-recovery/cases/${caseId}`, payload, { token });
          await loadDetail();
        }}
        onResolve={async () => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/billing-recovery/cases/${caseId}/resolve`, undefined, { token });
          await loadDetail();
        }}
      />
    </div>
  );
}
