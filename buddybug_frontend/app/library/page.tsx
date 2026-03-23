"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BookCard } from "@/components/BookCard";
import { BedtimeModeBadge } from "@/components/BedtimeModeBadge";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { OfflineBookBadge } from "@/components/OfflineBookBadge";
import { RecommendedBookCard } from "@/components/RecommendedBookCard";
import { SaveBookButton } from "@/components/SaveBookButton";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useFeatureFlags } from "@/context/FeatureFlagsContext";
import { useLocale } from "@/context/LocaleContext";
import { useParentalControls } from "@/context/ParentalControlsContext";
import {
  trackAgeBandFilteredByParentalControls,
  trackBedtimeModeUsed,
  trackLibraryViewed,
  trackRecommendationViewed,
} from "@/lib/analytics";
import { apiGet } from "@/lib/api";
import { fetchSavedLibrary } from "@/lib/library";
import { listOfflineBookPackages } from "@/lib/offline-storage";
import type {
  OfflineBookPackageRecord,
  RecommendationsResponse,
  RecommendedBookScore,
  ReaderBookSummary,
  UserLibraryItemRead,
} from "@/lib/types";

export default function LibraryPage() {
  const { hasPremiumAccess, isAuthenticated, token, user } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const { isEnabled } = useFeatureFlags();
  const { resolvedControls } = useParentalControls();
  const { locale, t } = useLocale();
  const [books, setBooks] = useState<ReaderBookSummary[]>([]);
  const [recommended, setRecommended] = useState<RecommendedBookScore[]>([]);
  const [savedItemsByBookId, setSavedItemsByBookId] = useState<Record<number, UserLibraryItemRead>>({});
  const [offlinePackagesByBookId, setOfflinePackagesByBookId] = useState<Record<number, OfflineBookPackageRecord>>({});
  const [selectedAgeBand, setSelectedAgeBand] = useState<"all" | "3-7" | "8-12">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const ageBand812Enabled = isEnabled("age_band_8_12_enabled");
  const offlineDownloadsEnabled = isEnabled("offline_downloads_enabled");
  const effectiveLanguage = selectedChildProfile?.language || locale;
  const effectiveAgeBand =
    selectedChildProfile?.age_band || (selectedAgeBand === "all" ? undefined : selectedAgeBand);
  const allowedAgeOptions =
    resolvedControls?.max_allowed_age_band === "3-7"
      ? (["all", "3-7"] as const)
      : ageBand812Enabled
        ? (["all", "3-7", "8-12"] as const)
        : (["all", "3-7"] as const);

  useEffect(() => {
    void trackLibraryViewed({
      token,
      user,
      language: effectiveLanguage,
      childProfileId: selectedChildProfile?.id,
    });
  }, [effectiveLanguage, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    if (resolvedControls?.bedtime_mode_enabled) {
      void trackBedtimeModeUsed(undefined, {
        token,
        user,
        language: effectiveLanguage,
        childProfileId: selectedChildProfile?.id,
        source: "library_page",
      });
    }
  }, [effectiveLanguage, resolvedControls?.bedtime_mode_enabled, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    if (resolvedControls?.max_allowed_age_band === "3-7" && selectedAgeBand === "8-12") {
      setSelectedAgeBand("3-7");
      void trackAgeBandFilteredByParentalControls({
        token,
        user,
        language: effectiveLanguage,
        childProfileId: selectedChildProfile?.id,
        source: "library_age_band_picker",
      });
    }
  }, [effectiveLanguage, resolvedControls?.max_allowed_age_band, selectedAgeBand, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    if (!ageBand812Enabled && selectedAgeBand === "8-12") {
      setSelectedAgeBand("3-7");
    }
  }, [ageBand812Enabled, selectedAgeBand]);

  useEffect(() => {
    async function loadOfflinePackages() {
      try {
        const packages = await listOfflineBookPackages();
        setOfflinePackagesByBookId(Object.fromEntries(packages.map((item) => [item.book_id, item])));
      } catch {
        setOfflinePackagesByBookId({});
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
    async function loadBooks() {
      try {
        const childProfileIdForRequest = isAuthenticated && token ? selectedChildProfile?.id : undefined;
        const [data, recommendations] = await Promise.all([
          apiGet<ReaderBookSummary[]>("/reader/books", {
            token,
            query: {
              language: effectiveLanguage,
              age_band: effectiveAgeBand,
              // Backend requires auth when `child_profile_id` is provided.
              child_profile_id: childProfileIdForRequest,
            },
          }),
          isAuthenticated
            ? apiGet<RecommendationsResponse>("/recommendations/me", {
                token,
                query: {
                  age_band: effectiveAgeBand,
                  child_profile_id: selectedChildProfile?.id,
                  limit: 4,
                },
              })
            : apiGet<RecommendationsResponse>("/recommendations/fallback", {
                query: {
                  language: effectiveLanguage,
                  age_band: effectiveAgeBand,
                  limit: 4,
                },
              }),
        ]);
        setBooks(data);
        setRecommended(recommendations.items.slice(0, 1));
        if (isAuthenticated && token) {
          const savedLibrary = await fetchSavedLibrary({
            token,
            childProfileId: selectedChildProfile?.id,
          });
          setSavedItemsByBookId(
            Object.fromEntries(savedLibrary.items.map((item) => [item.book_id, item])),
          );
        } else {
          setSavedItemsByBookId({});
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load books");
      } finally {
        setLoading(false);
      }
    }

    void loadBooks();
  }, [effectiveAgeBand, effectiveLanguage, isAuthenticated, selectedChildProfile?.id, token]);

  useEffect(() => {
    if (!recommended.length) {
      return;
    }
    void trackRecommendationViewed(
      recommended.map((item) => item.book_id),
      {
        token,
        user,
        language: effectiveLanguage,
        childProfileId: selectedChildProfile?.id,
        source: isAuthenticated ? "library_personalized" : "library_fallback",
      },
    );
  }, [effectiveLanguage, isAuthenticated, recommended, selectedChildProfile?.id, token, user]);

  if (loading) {
    return <LoadingState message="Loading published books..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load library" description={error} />;
  }

  if (!books.length) {
    return (
      <EmptyState
        title="No published books yet"
        description={
          selectedAgeBand === "all"
            ? selectedChildProfile
              ? `No published stories are available yet for ${selectedChildProfile.display_name}.`
              : "Once books are published from the backend workflow, they will appear here."
            : `No published ${selectedAgeBand} stories are available yet.`
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      {recommended.length ? (
        <section className="space-y-3">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">
              {isAuthenticated ? "Start here" : "Tonight's pick"}
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {isAuthenticated ? "One simple recommendation to get bedtime started." : "A gentle place to begin tonight."}
            </p>
          </div>
          <div className="grid gap-3">
            {recommended.map((item) => (
              <RecommendedBookCard
                key={`recommended-${item.book_id}`}
                item={item}
                reasonPrefix={t("recommendationReasonPrefix")}
                analyticsSource={isAuthenticated ? "library_personalized" : "library_fallback"}
                token={token}
                user={user}
              />
            ))}
          </div>
        </section>
      ) : null}

      <div>
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-2xl font-semibold text-slate-900">{t("libraryTitle")}</h2>
          {isAuthenticated ? (
            <Link
              href="/saved"
              className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900"
            >
              Saved books
            </Link>
          ) : null}
        </div>
        <p className="mt-1 text-sm text-slate-600">
          {t("libraryDescription")}
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <BedtimeModeBadge active={Boolean(resolvedControls?.bedtime_mode_enabled)} />
        </div>
        {selectedChildProfile ? (
          <p className="mt-3 inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-900">
            For {selectedChildProfile.display_name} • {selectedChildProfile.age_band} •{" "}
            {selectedChildProfile.language.toUpperCase()}
          </p>
        ) : (
          <div className="mt-3 flex flex-wrap gap-2">
            {allowedAgeOptions.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setSelectedAgeBand(option)}
                className={`rounded-full px-3 py-2 text-sm font-medium ${
                  selectedAgeBand === option
                    ? "bg-slate-900 text-white"
                    : "border border-slate-200 bg-white text-slate-700"
                }`}
              >
                {option === "all" ? "All ages" : option}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid gap-4">
        {books.map((book) => (
          <div key={book.book_id} className="space-y-3">
            <BookCard
              book={book}
              subtitle={
                hasPremiumAccess
                  ? `${book.page_count} pages • ${book.language.toUpperCase()} • ${t("fullAccess")}`
                  : `${book.page_count} pages • ${book.language.toUpperCase()} • ${t("previewAvailable")}`
              }
              statusLabel={hasPremiumAccess ? t("premium") : t("preview")}
            />
            <div className="flex items-center justify-between gap-3 rounded-3xl border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] px-4 py-3 text-white shadow-[0_20px_50px_rgba(30,41,59,0.16)]">
              <div className="flex flex-wrap gap-2">
                <OfflineBookBadge
                  availableOffline={Boolean(offlinePackagesByBookId[book.book_id])}
                  savedForOffline={Boolean(savedItemsByBookId[book.book_id]?.saved_for_offline)}
                  downloadedAt={savedItemsByBookId[book.book_id]?.downloaded_at}
                />
              </div>
              <SaveBookButton
                bookId={book.book_id}
                token={token}
                childProfileId={selectedChildProfile?.id}
                language={book.language}
                initialItem={savedItemsByBookId[book.book_id] ?? null}
                canSaveOffline={hasPremiumAccess && offlineDownloadsEnabled}
                onChanged={(item) =>
                  setSavedItemsByBookId((current) => {
                    const next = { ...current };
                    if (item) {
                      next[book.book_id] = item;
                    } else {
                      delete next[book.book_id];
                    }
                    return next;
                  })
                }
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
