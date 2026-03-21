"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { apiGet } from "@/lib/api";
import type { ChangelogEntryRead } from "@/lib/types";

function splitCsv(value: string | null) {
  return (value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function WhatsNewPage() {
  const [entries, setEntries] = useState<ChangelogEntryRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    void apiGet<ChangelogEntryRead[]>("/changelog")
      .then((response) => setEntries(response))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load what's new"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <LoadingState message="Loading what's new..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load what's new" description={error} />;
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:p-10">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">What’s New</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">Recent Buddybug updates</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
          A simple running log of new family-facing improvements as Buddybug grows.
        </p>
      </section>

      {entries.length ? (
        <div className="space-y-4">
          {entries.map((entry) => (
            <section key={entry.id} className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-slate-500">{entry.version_label}</p>
                  <h2 className="mt-1 text-2xl font-semibold text-slate-900">{entry.title}</h2>
                </div>
                <p className="text-sm text-slate-500">
                  {entry.published_at ? new Date(entry.published_at).toLocaleDateString() : "Recently updated"}
                </p>
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-700">{entry.summary}</p>
              {splitCsv(entry.area_tags).length ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {splitCsv(entry.area_tags).map((tag) => (
                    <span key={`${entry.id}-${tag}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                      {tag}
                    </span>
                  ))}
                </div>
              ) : null}
              {entry.details_markdown ? (
                <pre className="mt-4 whitespace-pre-wrap rounded-2xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">
                  {entry.details_markdown}
                </pre>
              ) : null}
            </section>
          ))}
        </div>
      ) : (
        <EmptyState title="No published updates yet" description="Buddybug will show family-facing release notes here once they are published." />
      )}
    </div>
  );
}
