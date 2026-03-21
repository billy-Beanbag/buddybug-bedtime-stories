"use client";

import { useEffect, useState } from "react";

import { BookCard } from "@/components/BookCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { apiGet } from "@/lib/api";
import { getReaderIdentifier } from "@/lib/auth";
import type { ContinueReadingResponse, ReaderBookSummary } from "@/lib/types";
import { useAuth } from "@/context/AuthContext";

export default function ContinueReadingPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [items, setItems] = useState<ContinueReadingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    async function loadContinueReading() {
      try {
        const readerIdentifier = getReaderIdentifier(user);
        const data = await apiGet<ContinueReadingResponse[]>("/reader/continue", {
          query: { reader_identifier: readerIdentifier },
        });
        setItems(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load continue reading");
      } finally {
        setLoading(false);
      }
    }

    void loadContinueReading();
  }, [authLoading, user]);

  if (authLoading || loading) {
    return <LoadingState message="Loading your reading activity..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load continue reading" description={error} />;
  }

  if (!items.length) {
    return (
      <EmptyState
        title="Nothing to continue yet"
        description="Open a story from the library and your progress will show up here."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Continue reading</h2>
        <p className="mt-1 text-sm text-slate-600">Jump back into your most recent stories.</p>
      </div>

      <div className="grid gap-4">
        {items.map((item) => {
          const bookLike: ReaderBookSummary = {
            book_id: item.book_id,
            title: item.title,
            cover_image_url: item.cover_image_url,
            age_band: "3-7",
            language: "en",
            published: true,
            publication_status: "published",
            page_count: 0,
          };

          return (
            <BookCard
              key={item.book_id}
              book={bookLike}
              subtitle={
                item.completed
                  ? `Finished • Last page ${item.current_page_number}`
                  : `Continue from page ${item.current_page_number}`
              }
              statusLabel={item.completed ? "Completed" : undefined}
              actionLabel={item.completed ? "Read again" : "Continue story"}
            />
          );
        })}
      </div>
    </div>
  );
}
