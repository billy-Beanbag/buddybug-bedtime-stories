"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { BookQueueList } from "@/components/admin/BookQueueList";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { AdminBookSummary } from "@/lib/types";

interface BookReadFallback {
  id: number;
  story_draft_id: number;
  title: string;
  age_band: string;
  language: string;
  content_lane_key?: string | null;
  publication_status: string;
  published: boolean;
  audio_available: boolean;
  created_at: string;
  updated_at: string;
}

export default function AdminBooksPage() {
  const { token } = useAuth();
  const [books, setBooks] = useState<AdminBookSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [publicationStatus, setPublicationStatus] = useState("");

  async function loadBooks() {
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<AdminBookSummary[]>("/admin/books/queue", {
        token,
        query: { publication_status: publicationStatus || undefined },
      });
      if (response.length > 0 || publicationStatus) {
        setBooks(response);
      } else {
        const fallback = await apiGet<BookReadFallback[]>("/books", {
          token,
          query: { limit: 100 },
        });
        setBooks(
          fallback.map((book) => ({
            id: book.id,
            story_draft_id: book.story_draft_id,
            title: book.title,
            age_band: book.age_band,
            language: book.language,
            content_lane_key: book.content_lane_key ?? null,
            publication_status: book.publication_status,
            published: book.published,
            audio_available: book.audio_available,
            created_at: book.created_at,
            updated_at: book.updated_at,
          })),
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load books queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadBooks();
  }, [token, publicationStatus]);

  if (loading) {
    return <LoadingState message="Loading books queue..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load books" description={error} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Books queue</h2>
          <p className="mt-1 text-sm text-slate-600">Publish or archive assembled books.</p>
        </div>
        <div className="flex gap-2">
          <select
            value={publicationStatus}
            onChange={(event) => setPublicationStatus(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="ready">Ready</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
          <button
            type="button"
            onClick={() => void loadBooks()}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Refresh
          </button>
        </div>
      </div>

      <BookQueueList books={books} token={token} onUpdated={loadBooks} />
    </div>
  );
}
