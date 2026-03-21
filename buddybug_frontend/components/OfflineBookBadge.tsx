"use client";

interface OfflineBookBadgeProps {
  availableOffline: boolean;
  savedForOffline?: boolean;
  downloadedAt?: string | null;
}

export function OfflineBookBadge({
  availableOffline,
  savedForOffline = false,
  downloadedAt = null,
}: OfflineBookBadgeProps) {
  if (!availableOffline && !savedForOffline && !downloadedAt) {
    return null;
  }

  const label = availableOffline ? "Available offline" : downloadedAt ? "Downloaded on another device" : "Saved for offline";
  const tone = availableOffline
    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
    : "border-indigo-200 bg-indigo-50 text-indigo-700";

  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${tone}`}>{label}</span>;
}
