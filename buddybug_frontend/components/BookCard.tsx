import Link from "next/link";

import { resolveApiUrl } from "@/lib/api";
import type { ReaderBookSummary } from "@/lib/types";

interface BookCardProps {
  book: ReaderBookSummary;
  subtitle?: string;
  statusLabel?: string;
  actionLabel?: string;
}

export function BookCard({
  book,
  subtitle,
  statusLabel,
  actionLabel = "Open story",
}: BookCardProps) {
  return (
    <Link
      href={`/reader/${book.book_id}`}
      className="group relative block overflow-hidden rounded-3xl border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-4 shadow-[0_24px_60px_rgba(30,41,59,0.2)] transition hover:-translate-y-0.5 hover:shadow-[0_28px_70px_rgba(30,41,59,0.24)]"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
      <div className="relative flex gap-4">
        <div className="h-28 w-20 shrink-0 overflow-hidden rounded-2xl bg-slate-900/40 ring-1 ring-white/10">
          {book.cover_image_url ? (
            <img
              src={resolveApiUrl(book.cover_image_url)}
              alt={book.title}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full items-center justify-center px-3 text-center text-xs text-indigo-100">
              No cover
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="text-base font-semibold leading-tight text-white">{book.title}</h2>
              {book.audio_available ? (
                <div className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-amber-200/30 bg-amber-200/12 px-2 py-1 text-[11px] font-medium text-amber-100">
                  <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                    <path d="M5 14h3l4 4V6L8 10H5z" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M16 9.5a4.5 4.5 0 0 1 0 5" strokeLinecap="round" />
                    <path d="M18.5 7a8 8 0 0 1 0 10" strokeLinecap="round" />
                  </svg>
                  <span>Audio</span>
                </div>
              ) : null}
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className="rounded-full border border-white/10 bg-white/10 px-2 py-1 text-xs font-medium text-indigo-100">
                {book.age_band}
              </span>
              {statusLabel ? (
                <span className="rounded-full border border-emerald-300/20 bg-emerald-300/15 px-2 py-1 text-xs font-medium text-emerald-100">
                  {statusLabel}
                </span>
              ) : null}
            </div>
          </div>
          <p className="mt-2 text-sm text-indigo-100">
            {subtitle || `${book.page_count} pages • ${book.language.toUpperCase()}`}
          </p>
          <p className="mt-4 text-sm font-medium text-white">{actionLabel}</p>
        </div>
      </div>
    </Link>
  );
}
