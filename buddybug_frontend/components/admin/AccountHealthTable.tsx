"use client";

import Link from "next/link";

import { HealthBandBadge } from "@/components/admin/HealthBandBadge";
import type { AccountHealthSnapshotResponse } from "@/lib/types";

export function AccountHealthTable({
  items,
  rebuildingUserId,
  onRebuild,
}: {
  items: AccountHealthSnapshotResponse[];
  rebuildingUserId: number | null;
  onRebuild: (userId: number) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Health</th>
              <th className="px-4 py-3 font-medium">Signals</th>
              <th className="px-4 py-3 font-medium">Dormancy</th>
              <th className="px-4 py-3 font-medium">Reasoning</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.snapshot.user_id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{item.user_display_name || item.user_email}</div>
                  <div className="mt-1 text-xs text-slate-500">{item.user_email}</div>
                  <div className="mt-1 text-xs text-slate-500">User #{item.snapshot.user_id}</div>
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="text-xl font-semibold text-slate-900">{item.snapshot.health_score}</div>
                  <div className="mt-2">
                    <HealthBandBadge band={item.snapshot.health_band} />
                  </div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div>Children: {item.snapshot.active_children_count}</div>
                  <div className="mt-1">Opens 30d: {item.snapshot.stories_opened_30d}</div>
                  <div className="mt-1">Completed 30d: {item.snapshot.stories_completed_30d}</div>
                  <div className="mt-1">Saved: {item.snapshot.saved_books_count}</div>
                  <div className="mt-1">Open tickets: {item.snapshot.support_tickets_open_count}</div>
                  <div className="mt-1">Premium: {item.snapshot.premium_status || "none"}</div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {item.snapshot.dormant_days !== null ? `${item.snapshot.dormant_days} days` : "n/a"}
                </td>
                <td className="max-w-sm px-4 py-4 align-top text-slate-600">
                  {item.snapshot.snapshot_reasoning || "No reasoning recorded."}
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void onRebuild(item.snapshot.user_id)}
                      disabled={rebuildingUserId === item.snapshot.user_id}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900 disabled:opacity-60"
                    >
                      {rebuildingUserId === item.snapshot.user_id ? "Rebuilding..." : "Rebuild"}
                    </button>
                    <Link
                      href={`/admin/lifecycle/${item.snapshot.user_id}`}
                      className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 font-medium text-slate-900"
                    >
                      Lifecycle
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
