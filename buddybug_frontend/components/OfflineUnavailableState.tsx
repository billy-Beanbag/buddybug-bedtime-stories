"use client";

import Link from "next/link";

interface OfflineUnavailableStateProps {
  title?: string;
  description?: string;
}

export function OfflineUnavailableState({
  title = "This story is not available right now",
  description = "Reconnect to Buddybug to open this story, or visit your saved library when you are back online.",
}: OfflineUnavailableStateProps) {
  return (
    <section className="space-y-3 rounded-[2rem] border border-dashed border-slate-300 bg-white/80 p-6 text-center shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
        <p className="mt-2 text-sm text-slate-600">{description}</p>
      </div>
      <Link
        href="/saved"
        className="inline-flex rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
      >
        Open saved books
      </Link>
    </section>
  );
}
