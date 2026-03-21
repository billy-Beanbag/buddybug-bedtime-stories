"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ActivityFeed } from "@/components/admin/ActivityFeed";
import { SupportTicketDetail } from "@/components/admin/SupportTicketDetail";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { SupportTicketDetailResponse } from "@/lib/types";

export default function AdminSupportTicketDetailPage() {
  const params = useParams<{ ticketId: string }>();
  const ticketId = Number(params.ticketId);
  const { token, isEditor } = useAuth();
  const [detail, setDetail] = useState<SupportTicketDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    if (!token || !ticketId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<SupportTicketDetailResponse>(`/admin/support/tickets/${ticketId}`, { token });
      setDetail(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load support ticket");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDetail();
  }, [ticketId, token]);

  if (!isEditor) {
    return <EmptyState title="Support access required" description="Only editor and admin users can open support operations." />;
  }

  if (loading) {
    return <LoadingState message="Loading support ticket..." />;
  }

  if (error || !detail) {
    return <EmptyState title="Unable to load support ticket" description={error || "Ticket not found."} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">Support ticket</p>
          <h2 className="text-2xl font-semibold text-slate-900">#{detail.ticket.id}</h2>
        </div>
        <div className="flex flex-wrap gap-3">
          {detail.ticket.user_id ? (
            <Link
              href={`/admin/lifecycle/${detail.ticket.user_id}`}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900"
            >
              User lifecycle
            </Link>
          ) : null}
          <Link
            href="/admin/support"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
          >
            Back to queue
          </Link>
        </div>
      </div>
      <SupportTicketDetail
        detail={detail}
        onUpdate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPatch(`/admin/support/tickets/${ticketId}`, payload, { token });
          await loadDetail();
        }}
        onAddNote={async (payload) => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/support/tickets/${ticketId}/notes`, payload, { token });
          await loadDetail();
        }}
        onResolve={async () => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/support/tickets/${ticketId}/resolve`, undefined, { token });
          await loadDetail();
        }}
        onClose={async () => {
          if (!token) {
            return;
          }
          await apiPost(`/admin/support/tickets/${ticketId}/close`, undefined, { token });
          await loadDetail();
        }}
      />
      <ActivityFeed token={token} entityType="support_ticket" entityId={ticketId} />
    </div>
  );
}
