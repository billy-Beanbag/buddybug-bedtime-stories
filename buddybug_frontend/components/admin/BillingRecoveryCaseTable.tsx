"use client";

import Link from "next/link";

import type { BillingRecoveryCaseRead } from "@/lib/types";

export function BillingRecoveryCaseTable({
  cases,
}: {
  cases: BillingRecoveryCaseRead[];
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Case</th>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Detected</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {cases.map((recoveryCase) => (
              <tr key={recoveryCase.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{recoveryCase.title}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {recoveryCase.source_type}
                    {recoveryCase.external_reference ? ` • ${recoveryCase.external_reference}` : ""}
                  </div>
                  <p className="mt-2 max-w-xl text-slate-600">{recoveryCase.summary}</p>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">#{recoveryCase.user_id}</td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div>{recoveryCase.recovery_status}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {recoveryCase.subscription_tier_snapshot || "unknown tier"} • {recoveryCase.billing_status_snapshot || "no snapshot"}
                  </div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div>{new Date(recoveryCase.first_detected_at).toLocaleString()}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    Last seen {new Date(recoveryCase.last_detected_at).toLocaleString()}
                  </div>
                </td>
                <td className="px-4 py-4 align-top">
                  <Link
                    href={`/admin/billing-recovery/${recoveryCase.id}`}
                    className="inline-flex rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                  >
                    Open case
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
