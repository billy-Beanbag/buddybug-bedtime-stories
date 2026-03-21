"use client";

export function HousekeepingRunButton({
  onRun,
  disabled,
  label,
}: {
  onRun: () => Promise<void>;
  disabled?: boolean;
  label?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => void onRun()}
      disabled={disabled}
      className="rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700 disabled:opacity-60"
    >
      {label || "Run"}
    </button>
  );
}
