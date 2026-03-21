"use client";

import type { OrganizationMembershipRead } from "@/lib/types";

const roleOptions = ["owner", "admin", "editor", "analyst", "support"] as const;

export function OrganizationMembersTable({
  memberships,
  updatingId,
  removingId,
  onRoleChange,
  onRemove,
}: {
  memberships: OrganizationMembershipRead[];
  updatingId: number | null;
  removingId: number | null;
  onRoleChange: (membership: OrganizationMembershipRead, role: string) => Promise<void>;
  onRemove: (membership: OrganizationMembershipRead) => Promise<void>;
}) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Team members</h2>
        <p className="mt-1 text-sm text-slate-600">A lightweight view of org memberships and roles for internal collaboration.</p>
      </div>
      <div className="mt-4 space-y-3">
        {memberships.map((membership) => (
          <div key={membership.id} className="grid gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-4 md:grid-cols-[1fr_180px_140px] md:items-center">
            <div>
              <p className="font-medium text-slate-900">User #{membership.user_id}</p>
              <p className="mt-1 text-xs text-slate-500">
                Added {new Date(membership.created_at).toLocaleString()} • {membership.is_active ? "Active" : "Inactive"}
              </p>
            </div>
            <select
              value={membership.role}
              onChange={(event) => void onRoleChange(membership, event.target.value)}
              disabled={updatingId === membership.id}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => void onRemove(membership)}
              disabled={removingId === membership.id}
              className="rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm font-medium text-rose-700 disabled:opacity-60"
            >
              {removingId === membership.id ? "Removing..." : "Remove"}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
