"use client";

import { useConnectivity } from "@/context/ConnectivityContext";

export function OfflineStatusBanner() {
  const { isOnline, pendingSyncCount } = useConnectivity();

  if (isOnline && pendingSyncCount === 0) {
    return null;
  }

  const message = isOnline
    ? `Back online. Syncing ${pendingSyncCount} queued update${pendingSyncCount === 1 ? "" : "s"}.`
    : `You are offline. Cached stories still work, and ${pendingSyncCount} update${pendingSyncCount === 1 ? "" : "s"} will sync later.`;

  return (
    <div
      className={`mb-4 rounded-3xl border px-4 py-3 text-sm shadow-sm ${
        isOnline ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-amber-200 bg-amber-50 text-amber-900"
      }`}
    >
      {message}
    </div>
  );
}
