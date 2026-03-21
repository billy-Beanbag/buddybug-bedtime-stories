"use client";

interface OfflineBadgeProps {
  savedForOffline: boolean;
  downloadedAt?: string | null;
}

export function OfflineBadge({ savedForOffline, downloadedAt }: OfflineBadgeProps) {
  if (!savedForOffline && !downloadedAt) {
    return null;
  }

  const label = downloadedAt ? "Offline-ready" : "Saved for offline";
  const tone = downloadedAt
    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
    : "border-indigo-200 bg-indigo-50 text-indigo-700";

  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${tone}`}>
      {label}
    </span>
  );
}
