"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SupportTicketQueue } from "@/components/admin/SupportTicketQueue";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type { SupportTicketListResponse, SupportTicketRead } from "@/lib/types";

export default function AdminSupportPage() {
  const { token, isEditor } = useAuth();
  const [tickets, setTickets] = useState<SupportTicketRead[]>([]);
  const [statusValue, setStatusValue] = useState("");
  const [priority, setPriority] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadTickets() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<SupportTicketListResponse>("/admin/support/tickets", {
        token,
        query: {
          status: statusValue || undefined,
          priority: priority || undefined,
          category: category || undefined,
        },
      });
      setTickets(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load support queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTickets();
  }, [category, priority, statusValue, token]);

  if (!isEditor) {
    return <EmptyState title="Support access required" description="Only editor and admin users can open support operations." />;
  }

  if (loading) {
    return <LoadingState message="Loading support queue..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load support queue" description={error} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Support queue</h2>
          <p className="mt-1 text-sm text-slate-600">Triage incoming bugs, billing issues, and parent questions.</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          <select
            value={statusValue}
            onChange={(event) => setStatusValue(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            {["open", "in_progress", "waiting_for_user", "resolved", "closed"].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All priorities</option>
            {["low", "normal", "high", "urgent"].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All categories</option>
            {[
              "general_support",
              "billing_issue",
              "bug_report",
              "content_concern",
              "feature_request",
              "parental_controls_question",
            ].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      {tickets.length ? (
        <SupportTicketQueue tickets={tickets} />
      ) : (
        <EmptyState title="No tickets match these filters" description="Try a different filter or wait for new requests." />
      )}
    </div>
  );
}
