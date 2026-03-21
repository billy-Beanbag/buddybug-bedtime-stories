"use client";

import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import type { ActivityFeedResponse } from "@/lib/types";

function formatMetadata(metadataJson: string | null) {
  if (!metadataJson) {
    return null;
  }
  try {
    const parsed = JSON.parse(metadataJson) as Record<string, unknown>;
    const entries = Object.entries(parsed).slice(0, 4);
    if (!entries.length) {
      return null;
    }
    return entries.map(([key, value]) => `${key}: ${String(value)}`).join(" • ");
  } catch {
    return metadataJson;
  }
}

export function ActivityFeed({
  token,
  entityType,
  entityId,
  userId,
  title = "Activity timeline",
}: {
  token: string | null;
  entityType?: string;
  entityId?: number;
  userId?: number;
  title?: string;
}) {
  const [items, setItems] = useState<ActivityFeedResponse["items"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    const path =
      typeof userId === "number"
        ? `/admin/activity/users/${userId}`
        : entityType && typeof entityId === "number"
          ? `/admin/activity/entity/${entityType}/${entityId}`
          : null;
    if (!path) {
      setLoading(false);
      setItems([]);
      return;
    }

    setLoading(true);
    setError(null);
    void apiGet<ActivityFeedResponse>(path, { token, query: { limit: 50 } })
      .then((response) => setItems(response.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load activity timeline"))
      .finally(() => setLoading(false));
  }, [entityId, entityType, token, userId]);

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        <p className="mt-1 text-sm text-slate-600">Recent audit and operational events for this record.</p>
      </div>

      {loading ? <p className="mt-4 text-sm text-slate-600">Loading activity...</p> : null}
      {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
      {!loading && !error && !items.length ? <p className="mt-4 text-sm text-slate-600">No activity recorded yet.</p> : null}

      {items.length ? (
        <div className="mt-4 space-y-3">
          {items.map((item, index) => (
            <div key={`${item.source_table}-${item.event_type}-${item.timestamp}-${index}`} className="rounded-2xl bg-slate-50 px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-medium text-slate-900">{item.summary}</p>
                <span className="text-xs text-slate-500">{new Date(item.timestamp).toLocaleString()}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {item.event_type} • {item.source_table}
                {item.actor_email ? ` • ${item.actor_email}` : item.actor_user_id ? ` • user #${item.actor_user_id}` : ""}
              </p>
              {formatMetadata(item.metadata_json) ? (
                <p className="mt-2 text-xs text-slate-600">{formatMetadata(item.metadata_json)}</p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
