"use client";

import Link from "next/link";

import { OfflineBookBadge } from "@/components/OfflineBookBadge";
import { resolveApiUrl } from "@/lib/api";
import type { ReaderBookSummary, ReaderDownloadAccessResponse, UserLibraryItemRead } from "@/lib/types";

interface SavedBookCardProps {
  book: ReaderBookSummary;
  item: UserLibraryItemRead;
  downloadAccess?: ReaderDownloadAccessResponse | null;
  offlineAvailable?: boolean;
  onDownload?: () => void;
  onRemoveOffline?: () => void;
}

export function SavedBookCard({
  book,
  item,
  downloadAccess,
  offlineAvailable = false,
  onDownload,
  onRemoveOffline,
}: SavedBookCardProps) {
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
            <OfflineBookBadge
              availableOffline={offlineAvailable}
              savedForOffline={item.saved_for_offline}
              downloadedAt={item.downloaded_at}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href={`/reader/${book.book_id}`}
              className="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            >
              Open story
            </Link>
            {downloadAccess?.can_download_full_book ? (
              <button
                type="button"
                onClick={onDownload}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900"
              >
                {offlineAvailable ? "Refresh offline copy" : "Save on this device"}
              </button>
            ) : null}
            {offlineAvailable && onRemoveOffline ? (
              <button
                type="button"
                onClick={onRemoveOffline}
                className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700"
              >
                Remove offline copy
              </button>
            ) : null}
          </div>
          {!downloadAccess?.can_download_full_book && downloadAccess ? (
            <p className="text-sm text-slate-600">{downloadAccess.reason}</p>
          ) : null}
        </div>
      </div>
    </article>
  );
}
