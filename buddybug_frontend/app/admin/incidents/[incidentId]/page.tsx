"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { IncidentDetail } from "@/components/admin/IncidentDetail";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { IncidentDetailResponse, RunbookEntryRead } from "@/lib/types";

export default function AdminIncidentDetailPage() {
  const params = useParams<{ incidentId: string }>();
  const incidentId = Number(params.incidentId);
  const { token, isAdmin } = useAuth();
  const [detail, setDetail] = useState<IncidentDetailResponse | null>(null);
  const [relatedRunbooks, setRelatedRunbooks] = useState<RunbookEntryRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    if (!token || !incidentId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const incidentResponse = await apiGet<IncidentDetailResponse>(`/admin/incidents/${incidentId}`, { token });
      setDetail(incidentResponse);
      const runbooksResponse = await apiGet<RunbookEntryRead[]>("/admin/runbooks", {
        token,
        query: {
          area: incidentResponse.incident.affected_area,
          is_active: true,
          limit: 20,
        },
      });
      setRelatedRunbooks(runbooksResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load incident");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadDetail();
    }
  }, [incidentId, token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage incident operations." />;
  }

  if (loading) {
    return <LoadingState message="Loading incident..." />;
  }

  if (error || !detail) {
    return <EmptyState title="Unable to load incident" description={error || "Incident not found."} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">Incident console</p>
          <h1 className="text-2xl font-semibold text-slate-900">#{detail.incident.id}</h1>
        </div>
        <Link
          href="/admin/incidents"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Back to incidents
        </Link>
      </div>

      <IncidentDetail
        detail={detail}
        relatedRunbooks={relatedRunbooks}
        onUpdate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPatch(`/admin/incidents/${incidentId}`, payload, { token });
          await loadDetail();
        }}
        onResolve={async (resolutionNote) => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/incidents/${incidentId}/resolve`, { body: resolutionNote || null }, { token });
          await loadDetail();
        }}
        onAddUpdate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/incidents/${incidentId}/updates`, payload, { token });
          await loadDetail();
        }}
      />
    </div>
  );
}
