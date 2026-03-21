"use client";

import type { ApiKeyRead } from "@/lib/types";

export function ApiKeyTable({
  apiKeys,
  deactivatingId,
  onDeactivate,
}: {
  apiKeys: ApiKeyRead[];
  deactivatingId: number | null;
  onDeactivate: (apiKey: ApiKeyRead) => Promise<void>;
}) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Issued API keys</h2>
        <p className="mt-1 text-sm text-slate-600">
          Buddybug stores only the key prefix and hash after creation. Use scopes to keep integrations narrow.
        </p>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="py-3 pr-4 font-medium">Name</th>
              <th className="py-3 pr-4 font-medium">Prefix</th>
              <th className="py-3 pr-4 font-medium">Scopes</th>
              <th className="py-3 pr-4 font-medium">Last used</th>
              <th className="py-3 pr-4 font-medium">Status</th>
              <th className="py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {apiKeys.map((apiKey) => (
              <tr key={apiKey.id} className="align-top text-slate-700">
                <td className="py-3 pr-4 font-medium text-slate-900">{apiKey.name}</td>
                <td className="py-3 pr-4 font-mono text-xs">{apiKey.key_prefix}</td>
                <td className="py-3 pr-4">{apiKey.scopes}</td>
                <td className="py-3 pr-4">{apiKey.last_used_at ? new Date(apiKey.last_used_at).toLocaleString() : "Never"}</td>
                <td className="py-3 pr-4">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      apiKey.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {apiKey.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="py-3">
                  {apiKey.is_active ? (
                    <button
                      type="button"
                      disabled={deactivatingId === apiKey.id}
                      onClick={() => void onDeactivate(apiKey)}
                      className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700 disabled:opacity-60"
                    >
                      {deactivatingId === apiKey.id ? "Deactivating..." : "Deactivate"}
                    </button>
                  ) : (
                    <span className="text-xs text-slate-500">Archived for auditability</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
