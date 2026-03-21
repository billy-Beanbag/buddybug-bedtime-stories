"use client";

import Link from "next/link";

import type { DailyStorySuggestionResponse } from "@/lib/types";

export function DailyStoryCard({
  dailyStory,
  label,
}: {
  dailyStory: DailyStorySuggestionResponse;
  label?: string;
}) {
  if (!dailyStory.suggestion || !dailyStory.book) {
    return (
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <p className="text-sm font-medium text-indigo-700">{label || "Today’s Story"}</p>
        <p className="mt-2 text-sm text-slate-600">A suitable story will appear here when one is available.</p>
      </section>
    );
  }

  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
      <p className="text-sm font-medium text-indigo-700">{label || "Today’s Story"}</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">{dailyStory.book.title}</h2>
      {dailyStory.suggestion.reason ? (
        <p className="mt-2 text-sm text-slate-600">{dailyStory.suggestion.reason}</p>
      ) : null}
      <p className="mt-2 text-xs text-slate-500">
        {dailyStory.book.age_band} • {dailyStory.book.language.toUpperCase()}
      </p>
      <Link
        href={`/reader/${dailyStory.book.book_id}`}
        className="mt-4 inline-flex rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
      >
        Open tonight’s pick
      </Link>
    </section>
  );
}
