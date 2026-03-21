"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SavedBookCard } from "@/components/SavedBookCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useConnectivity } from "@/context/ConnectivityContext";
import { useLocale } from "@/context/LocaleContext";
import { apiGet } from "@/lib/api";
import { trackOfflineBookSaved } from "@/lib/analytics";
import { downloadBookPackageForOffline, fetchDownloadAccess, fetchSavedLibrary, updateLibraryItem } from "@/lib/library";
import { queueSyncAction } from "@/lib/offline-sync";
import { listOfflineBookPackages, removeOfflineBookPackage } from "@/lib/offline-storage";
import type {
  OfflineBookPackageRecord,
  ReaderBookSummary,
  ReaderDownloadAccessResponse,
  UserLibraryItemRead,
} from "@/lib/types";

export default function SavedPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const { isOnline } = useConnectivity();
  const { locale } = useLocale();
  const [items, setItems] = useState<UserLibraryItemRead[]>([]);
  const [books, setBooks] = useState<ReaderBookSummary[]>([]);
  const [offlinePackages, setOfflinePackages] = useState<OfflineBookPackageRecord[]>([]);
  const [downloadAccessByBookId, setDownloadAccessByBookId] = useState<Record<number, ReaderDownloadAccessResponse>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const bookById = useMemo(
    () => Object.fromEntries(books.map((book) => [book.book_id, book])),
    [books],
  );
  const offlinePackageByBookId = useMemo(
    () => Object.fromEntries(offlinePackages.map((item) => [item.book_id, item])),
    [offlinePackages],
  );
  const offlineOnlyPackages = useMemo(
    () => offlinePackages.filter((item) => !items.some((savedItem) => savedItem.book_id === item.book_id)),
    [items, offlinePackages],
  );

  useEffect(() => {
    async function loadOfflinePackages() {
      try {
        setOfflinePackages(await listOfflineBookPackages());
      } catch {
        setOfflinePackages([]);
      }
    }

    void loadOfflinePackages();
    function handleOfflinePackagesChanged() {
      void loadOfflinePackages();
    }
    window.addEventListener("buddybug:offline-packages-changed", handleOfflinePackagesChanged as EventListener);
    return () => {
      window.removeEventListener("buddybug:offline-packages-changed", handleOfflinePackagesChanged as EventListener);
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setLoading(false);
      setItems([]);
      setBooks([]);
      setDownloadAccessByBookId({});
      return;
    }
    if (!isOnline) {
      setLoading(false);
      setError(null);
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

        const accessEntries = await Promise.all(
          savedLibrary.items
            .filter((item) => item.status === "saved")
            .map(async (item) => [
              item.book_id,
              await fetchDownloadAccess(item.book_id, {
                token: activeToken,
                language: selectedChildProfile?.language || locale,
              }),
            ] as const),
        );
        setDownloadAccessByBookId(Object.fromEntries(accessEntries));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load saved library");
      } finally {
        setLoading(false);
      }
    }

    void loadSavedLibrary();
  }, [isAuthenticated, isOnline, locale, selectedChildProfile?.id, selectedChildProfile?.language, token]);

  async function handleDownload(bookId: number) {
    if (!token) {
      return;
    }
    const { packageRecord, offlineRecord } = await downloadBookPackageForOffline(bookId, {
      token,
      language: selectedChildProfile?.language || locale,
      childProfileId: selectedChildProfile?.id,
    });
    void trackOfflineBookSaved(bookId, {
      token,
      language: offlineRecord.language,
      source: "saved_page",
      packageVersion: packageRecord.package_version,
    });
  }

  async function handleRemoveOfflineCopy(bookId: number, language: string) {
    await removeOfflineBookPackage(bookId, language);
    if (!token) {
      return;
    }
    if (isOnline) {
      await updateLibraryItem(
        bookId,
        { saved_for_offline: false },
        { token, childProfileId: selectedChildProfile?.id },
      ).catch(() => undefined);
      return;
    }
    await queueSyncAction("library_offline_state", {
      book_id: bookId,
      child_profile_id: selectedChildProfile?.id ?? null,
      saved_for_offline: false,
    });
  }

  if (authLoading || loading) {
    return <LoadingState message="Loading saved books..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Saved books are available for signed-in families"
          description="Sign in to keep a personal Buddybug library and prepare books for offline use."
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

  if (error && !offlinePackages.length) {
    return <EmptyState title="Unable to load saved books" description={error} />;
  }

  if (!items.length && !offlinePackages.length) {
    return (
      <EmptyState
        title="No saved books yet"
        description="Save stories from the library or reader to build a personal bedtime-ready collection."
      />
    );
  }

  return (
    <section className="space-y-4">
      <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Saved Library</h2>
        <p className="mt-1 text-sm text-slate-600">
          Keep favorite stories handy and prepare premium books for offline access.
        </p>
      </div>
      {!isOnline && offlinePackages.length ? (
        <div className="rounded-[2rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          You are offline. Showing stories already available on this device.
        </div>
      ) : null}
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
              downloadAccess={downloadAccessByBookId[item.book_id] ?? null}
              offlineAvailable={Boolean(offlinePackageByBookId[item.book_id])}
              onDownload={() => void handleDownload(item.book_id)}
              onRemoveOffline={() => void handleRemoveOfflineCopy(item.book_id, book.language)}
            />
          );
        })}
      </div>
      {offlineOnlyPackages.length ? (
        <section className="space-y-3 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">Available on this device</h3>
            <p className="mt-1 text-sm text-slate-600">These story packages can still open when Buddybug is offline.</p>
          </div>
          <div className="grid gap-3">
            {offlineOnlyPackages.map((offlinePackage) => (
              <div key={offlinePackage.key} className="rounded-3xl border border-slate-200 bg-white px-4 py-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h4 className="text-base font-semibold text-slate-900">{offlinePackage.title}</h4>
                    <p className="mt-1 text-sm text-slate-600">
                      {offlinePackage.language.toUpperCase()} • {offlinePackage.age_band} • version {offlinePackage.package_version}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      href={`/reader/${offlinePackage.book_id}`}
                      className="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-medium text-white"
                    >
                      Open offline
                    </Link>
                    <button
                      type="button"
                      onClick={() => void handleRemoveOfflineCopy(offlinePackage.book_id, offlinePackage.language)}
                      className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700"
                    >
                      Remove copy
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}
