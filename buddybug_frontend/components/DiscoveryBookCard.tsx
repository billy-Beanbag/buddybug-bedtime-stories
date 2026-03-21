"use client";

import Link from "next/link";

import { trackDiscoveryBookOpened } from "@/lib/analytics";
import { resolveApiUrl } from "@/lib/api";
import type { DiscoverySearchResult, User } from "@/lib/types";

export function DiscoveryBookCard({
  book,
  token,
  user,
  childProfileId,
}: {
  book: DiscoverySearchResult;
  token?: string | null;
  user?: User | null;
  childProfileId?: number | null;
}) {
  const subtitle = book.reasons?.[0] || `${book.language.toUpperCase()} • ${book.age_band}`;

  return (
    <Link
      href={`/reader/${book.book_id}`}
      onClick={() => {
        void trackDiscoveryBookOpened(book.book_id, {
          token,
          user,
          childProfileId,
          language: book.language,
          source: "discovery_card",
        });
      }}
      className="block rounded-3xl border border-white/70 bg-white/85 p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex gap-4">
        <div className="h-24 w-20 shrink-0 overflow-hidden rounded-2xl bg-slate-200">
          {book.cover_image_url ? (
            <img src={resolveApiUrl(book.cover_image_url)} alt={book.title} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center px-2 text-center text-xs text-slate-500">No cover</div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-base font-semibold leading-tight text-slate-900">{book.title}</h3>
            <span className="rounded-full bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700">{book.age_band}</span>
          </div>
          <p className="mt-2 text-sm text-slate-600">{subtitle}</p>
          <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">
            {book.language.toUpperCase()} {book.content_lane_key ? `• ${book.content_lane_key}` : ""}
          </p>
        </div>
      </div>
    </Link>
  );
}
