"use client";

import Link from "next/link";
import { useState } from "react";

import { apiPost } from "@/lib/api";
import type { AdminBookSummary } from "@/lib/types";

export function BookQueueList({
  books,
  token,
  onUpdated,
}: {
  books: AdminBookSummary[];
  token: string | null;
  onUpdated: () => Promise<void> | void;
}) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function getReaderHref(book: AdminBookSummary) {
    return book.published || book.publication_status === "published"
      ? `/reader/${book.id}`
      : `/reader/${book.id}?preview=1`;
  }

  async function handleAction(bookId: number, action: "publish" | "archive") {
    if (!token) {
      return;
    }

    setBusyId(bookId);
    setMessage(null);
    setError(null);
    try {
      await apiPost(`/books/${bookId}/${action}`, undefined, { token });
      setMessage(`Book ${action}ed.`);
      await onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Unable to ${action} book`);
    } finally {
      setBusyId(null);
    }
  }

  if (!books.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        No books are in this queue right now.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {books.map((book) => (
        <div key={book.id} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-900">{book.title}</h3>
              <p className="mt-1 text-sm text-slate-600">Status: {book.publication_status}</p>
              <p className="mt-1 text-sm text-slate-600">
                Published: {book.published ? "Yes" : "No"} • Audio: {book.audio_available ? "Available" : "Not ready"}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href={getReaderHref(book)}
                className="rounded-2xl bg-sky-50 px-4 py-2 text-sm font-medium text-sky-800"
              >
                View book
              </Link>
              <button
                type="button"
                disabled={busyId === book.id}
                onClick={() => handleAction(book.id, "publish")}
                className="rounded-2xl bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 disabled:opacity-60"
              >
                Publish
              </button>
              <button
                type="button"
                disabled={busyId === book.id}
                onClick={() => handleAction(book.id, "archive")}
                className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-medium text-slate-800 disabled:opacity-60"
              >
                Archive
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
