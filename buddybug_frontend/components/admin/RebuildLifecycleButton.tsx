"use client";

export function RebuildLifecycleButton({
  rebuilding,
  onRebuild,
}: {
  rebuilding: boolean;
  onRebuild: () => Promise<void>;
}) {
  return (
    <button
      type="button"
      onClick={() => void onRebuild()}
      disabled={rebuilding}
      className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
    >
      {rebuilding ? "Rebuilding..." : "Rebuild lifecycle"}
    </button>
  );
}
