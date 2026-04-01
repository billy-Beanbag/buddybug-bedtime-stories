"use client";

import Link from "next/link";
import { useState } from "react";

import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { AdminBookSummary, ReaderPageRead } from "@/lib/types";

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
  const [editingBookId, setEditingBookId] = useState<number | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftPages, setDraftPages] = useState<ReaderPageRead[]>([]);

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

  async function startEditing(book: AdminBookSummary) {
    if (!token) {
      return;
    }
    setEditingBookId(book.id);
    setDraftTitle(book.title);
    setBusyId(book.id);
    setMessage(null);
    setError(null);
    try {
      const pages = await apiGet<ReaderPageRead[]>(`/books/${book.id}/pages`, { token });
      setDraftPages(pages.filter((page) => page.page_number > 0));
    } catch (err) {
      setEditingBookId(null);
      setDraftPages([]);
      setError(err instanceof Error ? err.message : "Unable to load book pages");
    } finally {
      setBusyId(null);
    }
  }

  async function handleSaveTitle(book: AdminBookSummary) {
    if (!token) {
      return;
    }

    const trimmedTitle = draftTitle.trim();
    if (!trimmedTitle) {
      setError("Title cannot be empty.");
      return;
    }

    setBusyId(book.id);
    setMessage(null);
    setError(null);
    try {
      const requests: Array<Promise<unknown>> = [];
      if (trimmedTitle !== book.title) {
        requests.push(apiPatch(`/books/${book.id}`, { title: trimmedTitle }, { token }));
        requests.push(apiPatch(`/story-drafts/${book.story_draft_id}`, { title: trimmedTitle }, { token }));
      }

      for (const page of draftPages) {
        const normalizedText = page.text_content.trim();
        requests.push(apiPatch(`/books/${book.id}/pages/${page.page_number}`, { text_content: normalizedText }, { token }));
        if (page.source_story_page_id) {
          requests.push(apiPatch(`/story-pages/${page.source_story_page_id}`, { page_text: normalizedText }, { token }));
        }
      }

      await Promise.all(requests);
      setMessage("Book updates saved.");
      setEditingBookId(null);
      setDraftPages([]);
      await onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update book");
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
              {editingBookId === book.id ? (
                <div className="space-y-2">
                  <label className="block">
                    <span className="sr-only">Book title</span>
                    <input
                      type="text"
                      value={draftTitle}
                      onChange={(event) => setDraftTitle(event.target.value)}
                      className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900"
                    />
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busyId === book.id}
                      onClick={() => void handleSaveTitle(book)}
                      className="rounded-2xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      disabled={busyId === book.id}
                      onClick={() => {
                        setEditingBookId(null);
                        setDraftTitle("");
                        setDraftPages([]);
                      }}
                      className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-medium text-slate-800 disabled:opacity-60"
                    >
                      Cancel
                    </button>
                  </div>
                  {draftPages.length ? (
                    <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Story pages</p>
                      {draftPages.map((page) => (
                        <label key={page.id} className="block space-y-1">
                          <span className="text-xs font-medium text-slate-600">Page {page.page_number}</span>
                          <textarea
                            value={page.text_content}
                            onChange={(event) =>
                              setDraftPages((current) =>
                                current.map((entry) =>
                                  entry.id === page.id ? { ...entry, text_content: event.target.value } : entry,
                                ),
                              )
                            }
                            rows={3}
                            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
                          />
                        </label>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <h3 className="text-base font-semibold text-slate-900">{book.title}</h3>
              )}
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
                onClick={() => void startEditing(book)}
                className="rounded-2xl bg-violet-50 px-4 py-2 text-sm font-medium text-violet-800 disabled:opacity-60"
              >
                Edit
              </button>
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
