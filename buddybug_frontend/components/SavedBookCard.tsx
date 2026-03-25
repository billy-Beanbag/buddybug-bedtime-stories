"use client";

import Link from "next/link";

import { resolveApiUrl } from "@/lib/api";
import type { ReaderBookSummary, UserLibraryItemRead } from "@/lib/types";

interface SavedBookCardProps {
  book: ReaderBookSummary;
  item: UserLibraryItemRead;
}

export function SavedBookCard({ book, item }: SavedBookCardProps) {
  return (
    <article className="rounded-3xl border border-white/70 bg-white/85 p-4 shadow-sm">
      <div className="flex gap-4">
        <div className="h-28 w-20 shrink-0 overflow-hidden rounded-2xl bg-slate-200">
          {book.cover_image_url ? (
            <img src={resolveApiUrl(book.cover_image_url)} alt={book.title} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center px-3 text-center text-xs text-slate-500">No cover</div>
          )}
        </div>
        <div className="min-w-0 flex-1 space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold leading-tight text-slate-900">{book.title}</h2>
              <p className="mt-1 text-sm text-slate-600">
                {book.page_count} pages • {book.language.toUpperCase()} • {book.age_band}
              </p>
            </div>
            <span className="inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">
              {item.status === "saved" ? "Saved" : "Library"}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href={`/reader/${book.book_id}`}
              className="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            >
              Open story
            </Link>
          </div>
          <p className="text-sm text-slate-600">Saved to your Buddybug library for quick access the next time you sign in.</p>
        </div>
      </div>
    </article>
  );
}
