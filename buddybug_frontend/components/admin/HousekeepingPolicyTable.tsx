"use client";

import type { HousekeepingPolicyRead } from "@/lib/types";

import { HousekeepingRunButton } from "./HousekeepingRunButton";

export function HousekeepingPolicyTable({
  policies,
  runningPolicyId,
  onRun,
}: {
  policies: HousekeepingPolicyRead[];
  runningPolicyId: number | null;
  onRun: (policy: HousekeepingPolicyRead, dryRunOverride?: boolean) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Policy</th>
              <th className="px-4 py-3 font-medium">Target</th>
              <th className="px-4 py-3 font-medium">Action</th>
              <th className="px-4 py-3 font-medium">Retention</th>
              <th className="px-4 py-3 font-medium">Mode</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {policies.map((policy) => (
              <tr key={policy.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{policy.name}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {policy.key} • #{policy.id}
                  </div>
                  {policy.notes ? <p className="mt-2 max-w-xl text-slate-600">{policy.notes}</p> : null}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{policy.target_table}</td>
                <td className="px-4 py-4 align-top text-slate-700">{policy.action_type}</td>
                <td className="px-4 py-4 align-top text-slate-700">{policy.retention_days} days</td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${policy.enabled ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
                      {policy.enabled ? "enabled" : "disabled"}
                    </span>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${policy.dry_run_only ? "bg-sky-50 text-sky-700" : "bg-amber-50 text-amber-700"}`}>
                      {policy.dry_run_only ? "dry-run only" : "active allowed"}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <HousekeepingRunButton
                      onRun={async () => onRun(policy, true)}
                      disabled={runningPolicyId === policy.id || !policy.enabled}
                      label={runningPolicyId === policy.id ? "Running..." : "Dry run"}
                    />
                    {!policy.dry_run_only ? (
                      <button
                        type="button"
                        onClick={() => void onRun(policy, false)}
                        disabled={runningPolicyId === policy.id || !policy.enabled}
                        className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700 disabled:opacity-60"
                      >
                        Active run
                      </button>
                    ) : null}
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
