"use client";

import Link from "next/link";

import type { StoryQualityQueueItemResponse } from "@/lib/types";

export function StoryQualityCard({ item }: { item: StoryQualityQueueItemResponse }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-slate-900">{item.title}</h3>
          <p className="mt-1 text-sm text-slate-600">{item.evaluation_summary || "Automated review found items to inspect."}</p>
        </div>
        <div className="shrink-0 space-y-2 text-right text-sm">
          <div
            className={`rounded-full px-3 py-1 font-medium ${
              item.quality_score < 70 ? "bg-rose-50 text-rose-700" : "bg-amber-50 text-amber-700"
            }`}
          >
            Score {item.quality_score}
          </div>
          <p className="text-slate-500">{item.review_status}</p>
        </div>
      </div>

      {item.flagged_issues.length ? (
        <ul className="mt-4 space-y-2 text-sm text-slate-700">
          {item.flagged_issues.slice(0, 4).map((issue) => (
            <li key={issue} className="rounded-2xl bg-slate-50 px-3 py-2">
              {issue}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-4 flex gap-2">
        <Link
          href={`/admin/drafts/${item.story_id}`}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
        >
          Open draft review
        </Link>
        <Link
          href={`/admin/story-quality`}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Stay in queue
        </Link>
      </div>
    </article>
  );
}
