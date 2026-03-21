"use client";

import type { BetaCohortMembershipRead } from "@/lib/types";

export function BetaMembershipTable({
  memberships,
  updatingMembershipId,
  onToggleActive,
}: {
  memberships: BetaCohortMembershipRead[];
  updatingMembershipId: number | null;
  onToggleActive: (membership: BetaCohortMembershipRead, nextActive: boolean) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Joined</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {memberships.map((membership) => (
              <tr key={membership.id}>
                <td className="px-4 py-4 align-top text-slate-900">User #{membership.user_id}</td>
                <td className="px-4 py-4 align-top text-slate-700">{membership.source}</td>
                <td className="px-4 py-4 align-top">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${membership.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
                    {membership.is_active ? "active" : "inactive"}
                  </span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{new Date(membership.joined_at).toLocaleString()}</td>
                <td className="px-4 py-4 align-top">
                  <button
                    type="button"
                    onClick={() => void onToggleActive(membership, !membership.is_active)}
                    disabled={updatingMembershipId === membership.id}
                    className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900 disabled:opacity-60"
                  >
                    {updatingMembershipId === membership.id
                      ? "Saving..."
                      : membership.is_active
                        ? "Deactivate"
                        : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
