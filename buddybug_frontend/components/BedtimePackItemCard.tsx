"use client";

import Link from "next/link";

import type { BedtimePackItemRead } from "@/lib/types";

interface BedtimePackItemCardProps {
  item: BedtimePackItemRead;
  isCurrent?: boolean;
  onOpen?: (item: BedtimePackItemRead) => Promise<void> | void;
  onComplete?: (item: BedtimePackItemRead) => Promise<void> | void;
  loadingAction?: "open" | "complete" | null;
}

export function BedtimePackItemCard({
  item,
  isCurrent = false,
  onOpen,
  onComplete,
  loadingAction = null,
}: BedtimePackItemCardProps) {
  return (
    <article
      className={`relative space-y-3 overflow-hidden rounded-[2rem] border p-4 text-white shadow-[0_24px_60px_rgba(30,41,59,0.16)] ${
        isCurrent
          ? "border-indigo-200/30 bg-[linear-gradient(135deg,#1e1b4b_0%,#312e81_55%,#4338ca_100%)]"
          : "border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)]"
      }`}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.16),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
      <div className="relative space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-indigo-100">Story {item.position}</p>
          <h3 className="mt-1 text-lg font-semibold text-white">Book #{item.book_id}</h3>
          <p className="mt-1 text-sm text-indigo-100">
            {item.recommended_narration ? "Narration would fit nicely here." : "A calm read-together moment."}
          </p>
        </div>
        <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-indigo-100">
          {item.completion_status}
        </span>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link
          href={`/reader/${item.book_id}`}
          onClick={() => {
            void onOpen?.(item);
          }}
          className="rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white"
        >
          Open story
        </Link>
        {item.completion_status !== "completed" && onComplete ? (
          <button
            type="button"
            onClick={() => void onComplete(item)}
            disabled={loadingAction === "complete"}
            className="rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {loadingAction === "complete" ? "Saving..." : "Mark complete"}
          </button>
        ) : null}
      </div>
      </div>
    </article>
  );
}
