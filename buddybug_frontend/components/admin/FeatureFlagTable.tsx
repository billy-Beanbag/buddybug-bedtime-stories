"use client";

import type { FeatureFlagRead } from "@/lib/types";

interface FeatureFlagTableProps {
  flags: FeatureFlagRead[];
  deletingId?: number | null;
  onEdit: (flag: FeatureFlagRead) => void;
  onDelete: (flag: FeatureFlagRead) => Promise<void>;
}

function summarizeTargets(flag: FeatureFlagRead) {
  return [
    flag.environments ? `env: ${flag.environments}` : null,
    flag.target_subscription_tiers ? `tiers: ${flag.target_subscription_tiers}` : null,
    flag.target_languages ? `lang: ${flag.target_languages}` : null,
    flag.target_age_bands ? `age: ${flag.target_age_bands}` : null,
    flag.target_roles ? `roles: ${flag.target_roles}` : null,
    flag.target_user_ids ? `users: ${flag.target_user_ids}` : null,
    flag.target_countries ? `countries: ${flag.target_countries}` : null,
    flag.target_beta_cohorts ? `beta: ${flag.target_beta_cohorts}` : null,
    flag.is_internal_only ? "internal only" : null,
  ]
    .filter(Boolean)
    .join(" • ");
}

export function FeatureFlagTable({ flags, deletingId = null, onEdit, onDelete }: FeatureFlagTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Flag</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Targets</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {flags.map((flag) => (
              <tr key={flag.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{flag.name}</div>
                  <div className="mt-1 font-mono text-xs text-slate-500">{flag.key}</div>
                  {flag.description ? <p className="mt-2 max-w-md text-slate-600">{flag.description}</p> : null}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div>{flag.enabled ? "Enabled" : "Disabled"}</div>
                  <div className="mt-1 text-xs text-slate-500">Rollout {flag.rollout_percentage}%</div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {summarizeTargets(flag) || "All contexts"}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {new Date(flag.updated_at).toLocaleString()}
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onEdit(flag)}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => void onDelete(flag)}
                      disabled={deletingId === flag.id}
                      className="rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 font-medium text-rose-700 disabled:opacity-60"
                    >
                      {deletingId === flag.id ? "Deleting..." : "Delete"}
                    </button>
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
