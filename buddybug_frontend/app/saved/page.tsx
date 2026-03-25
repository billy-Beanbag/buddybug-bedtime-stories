"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SavedBookCard } from "@/components/SavedBookCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import { apiGet } from "@/lib/api";
import { fetchSavedLibrary } from "@/lib/library";
import type { ReaderBookSummary, UserLibraryItemRead } from "@/lib/types";

export default function SavedPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const { locale } = useLocale();
  const [items, setItems] = useState<UserLibraryItemRead[]>([]);
  const [books, setBooks] = useState<ReaderBookSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const bookById = useMemo(
    () => Object.fromEntries(books.map((book) => [book.book_id, book])),
    [books],
  );

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setLoading(false);
      setItems([]);
      setBooks([]);
      return;
    }
    const activeToken = token;

    async function loadSavedLibrary() {
      setLoading(true);
      setError(null);
      try {
        const [savedLibrary, readerBooks] = await Promise.all([
          fetchSavedLibrary({ token: activeToken, childProfileId: selectedChildProfile?.id }),
          apiGet<ReaderBookSummary[]>("/reader/books", {
            token: activeToken,
            query: {
              language: selectedChildProfile?.language || locale,
              child_profile_id: selectedChildProfile?.id,
            },
          }),
        ]);
        setItems(savedLibrary.items.filter((item) => item.status === "saved"));
        setBooks(readerBooks);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load saved library");
      } finally {
        setLoading(false);
      }
    }

    void loadSavedLibrary();
  }, [isAuthenticated, locale, selectedChildProfile?.id, selectedChildProfile?.language, token]);

  if (authLoading || loading) {
    return <LoadingState message="Loading saved books..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Saved books are available for signed-in families"
          description="Sign in to keep a personal Buddybug library of stories you want to come back to later."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Log in
          </Link>
          <Link href="/register" className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white">
            Create account
          </Link>
        </div>
      </div>
    );
  }

  if (error) {
    return <EmptyState title="Unable to load saved books" description={error} />;
  }

  if (!items.length) {
    return (
      <EmptyState
        title="No saved books yet"
        description="Save stories from the library or reader to build your personal Buddybug library."
      />
    );
  }

  return (
    <section className="space-y-4">
      <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Saved Library</h2>
        <p className="mt-1 text-sm text-slate-600">
          Stories saved here are kept in your Buddybug account so they are easy to find again whenever you sign in.
        </p>
      </div>
      <div className="grid gap-4">
        {items.map((item) => {
          const book = bookById[item.book_id];
          if (!book) {
            return null;
          }
          return (
            <SavedBookCard
              key={item.id}
              book={book}
              item={item}
            />
          );
        })}
      </div>
    </section>
  );
}
