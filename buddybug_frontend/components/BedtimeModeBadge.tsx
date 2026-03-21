"use client";

export function BedtimeModeBadge({ active }: { active: boolean }) {
  if (!active) {
    return null;
  }

  return (
    <span className="inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-900">
      Bedtime mode
    </span>
  );
}
