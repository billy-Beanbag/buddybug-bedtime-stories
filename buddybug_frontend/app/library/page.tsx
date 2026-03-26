"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { BookCard } from "@/components/BookCard";
import { BedtimeModeBadge } from "@/components/BedtimeModeBadge";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
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
import type { RecommendationsResponse, RecommendedBookScore, ReaderBookSummary, UserLibraryItemRead } from "@/lib/types";

const BEDTIME_LANE = "bedtime_3_7";
const ADVENTURE_LANE = "story_adventures_3_7";
const LIBRARY_ROUTE_STORAGE_KEY = "buddybug.library-route";

type LibraryRouteFilter = "all" | typeof BEDTIME_LANE | typeof ADVENTURE_LANE;

const LIBRARY_ROUTE_OPTIONS: Array<{
  key: LibraryRouteFilter;
  label: string;
  description: string;
}> = [
  { key: "all", label: "All stories", description: "Show every published 3-7 story in this view." },
  { key: BEDTIME_LANE, label: "Bedtime stories", description: "Calm, cosy stories for winding down." },
  { key: ADVENTURE_LANE, label: "Adventure stories", description: "Playful, plot-led stories with more energy." },
];

function readStoredLibraryRoute(): LibraryRouteFilter {
  if (typeof window === "undefined") {
    return "all";
  }
  const stored = window.localStorage.getItem(LIBRARY_ROUTE_STORAGE_KEY);
  if (stored === BEDTIME_LANE || stored === ADVENTURE_LANE || stored === "all") {
    return stored;
  }
  return "all";
}

function persistLibraryRoute(route: LibraryRouteFilter) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(LIBRARY_ROUTE_STORAGE_KEY, route);
}

function matchesRoute(route: LibraryRouteFilter, laneKey: string | null | undefined) {
  return route === "all" || laneKey === route;
}

export default function LibraryPage() {
  const { hasPremiumAccess, isAuthenticated, token, user } = useAuth();
  const { selectedChildProfile, isLoading: childProfilesLoading } = useChildProfiles();
  const { isEnabled } = useFeatureFlags();
  const { resolvedControls, isLoading: parentalControlsLoading } = useParentalControls();
  const { locale, t } = useLocale();
  const [books, setBooks] = useState<ReaderBookSummary[]>([]);
  const [recommended, setRecommended] = useState<RecommendedBookScore[]>([]);
  const [savedItemsByBookId, setSavedItemsByBookId] = useState<Record<number, UserLibraryItemRead>>({});
  const [selectedAgeBand, setSelectedAgeBand] = useState<"all" | "3-7" | "8-12">("all");
  const [selectedRoute, setSelectedRoute] = useState<LibraryRouteFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const ageBand812Enabled = isEnabled("age_band_8_12_enabled");
  const effectiveLanguage = selectedChildProfile?.language || locale;
  const effectiveAgeBand =
    selectedChildProfile?.age_band || (selectedAgeBand === "all" ? undefined : selectedAgeBand);
  const allowedAgeOptions =
    resolvedControls?.max_allowed_age_band === "3-7"
      ? (["all", "3-7"] as const)
      : ageBand812Enabled
        ? (["all", "3-7", "8-12"] as const)
        : (["all", "3-7"] as const);
  const routeFilteredRecommended = useMemo(
    () => recommended.filter((item) => matchesRoute(selectedRoute, item.content_lane_key)),
    [recommended, selectedRoute],
  );
  const bedtimeModeBlocksAdventure = Boolean(
    selectedRoute === ADVENTURE_LANE && resolvedControls?.bedtime_mode_enabled,
  );

  useEffect(() => {
    setSelectedRoute(readStoredLibraryRoute());
  }, []);

  useEffect(() => {
    persistLibraryRoute(selectedRoute);
  }, [selectedRoute]);

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
    async function loadBooks() {
      if (isAuthenticated && (childProfilesLoading || parentalControlsLoading)) {
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const childProfileIdForRequest = isAuthenticated && token ? selectedChildProfile?.id : undefined;
        const [data, recommendations] = await Promise.all([
          apiGet<ReaderBookSummary[]>("/reader/books", {
            token,
            query: {
              language: effectiveLanguage,
              age_band: effectiveAgeBand,
              content_lane_key: selectedRoute === "all" ? undefined : selectedRoute,
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
  }, [
    childProfilesLoading,
    effectiveAgeBand,
    effectiveLanguage,
    isAuthenticated,
    parentalControlsLoading,
    selectedRoute,
    selectedChildProfile?.id,
    token,
  ]);

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

  if (loading || (isAuthenticated && (childProfilesLoading || parentalControlsLoading))) {
    return <LoadingState message="Loading published books..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load library" description={error} />;
  }

  const emptyStateTitle = bedtimeModeBlocksAdventure
    ? "Adventure stories are hidden right now"
    : "No published books yet";
  const emptyStateDescription = bedtimeModeBlocksAdventure
    ? selectedChildProfile
      ? `Adventure stories for ${selectedChildProfile.display_name} are currently hidden because Bedtime mode is on. Switch to Bedtime or All stories, or turn Bedtime mode off when you want a more energetic read.`
      : "Adventure stories are currently hidden because Bedtime mode is on. Switch to Bedtime or All stories, or turn Bedtime mode off when you want a more energetic read."
    : selectedRoute === BEDTIME_LANE
      ? "No bedtime stories are published yet for this view."
      : selectedRoute === ADVENTURE_LANE
        ? "No adventure stories are published yet for this view."
        : selectedAgeBand === "all"
          ? selectedChildProfile
            ? resolvedControls?.bedtime_mode_enabled
              ? `No published stories are currently visible for ${selectedChildProfile.display_name}. Bedtime mode or parental controls may be hiding adventure stories.`
              : `No published stories are available yet for ${selectedChildProfile.display_name}.`
            : "Once books are published from the backend workflow, they will appear here."
          : `No published ${selectedAgeBand} stories are available yet.`;

  return (
    <div className="space-y-4">
      {routeFilteredRecommended.length ? (
        <section className="space-y-3">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">
              {selectedRoute === ADVENTURE_LANE ? "Adventure pick" : isAuthenticated ? "Start here" : "Tonight's pick"}
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {selectedRoute === ADVENTURE_LANE
                ? "A story with a little more energy for today's reading session."
                : isAuthenticated
                  ? "One simple recommendation to get bedtime started."
                  : "A gentle place to begin tonight."}
            </p>
          </div>
          <div className="grid gap-3">
            {routeFilteredRecommended.map((item) => (
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
        <div className="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Choose your story route</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {LIBRARY_ROUTE_OPTIONS.map((route) => (
              <button
                key={route.key}
                type="button"
                onClick={() => setSelectedRoute(route.key)}
                className={`rounded-2xl border px-4 py-3 text-left transition ${
                  selectedRoute === route.key
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-slate-50 text-slate-900 hover:bg-slate-100"
                }`}
              >
                <div className="text-sm font-semibold">{route.label}</div>
                <div className={`mt-1 text-xs ${selectedRoute === route.key ? "text-slate-200" : "text-slate-600"}`}>
                  {route.description}
                </div>
              </button>
            ))}
          </div>
          {bedtimeModeBlocksAdventure ? (
            <p className="mt-3 text-sm text-amber-700">
              Bedtime mode is currently hiding adventure stories. Switch to Bedtime or All stories, or turn Bedtime mode
              off when you want a more energetic read.
            </p>
          ) : null}
        </div>
        {isAuthenticated ? (
          <div className="mt-4 rounded-3xl border border-indigo-200 bg-[linear-gradient(135deg,rgba(238,242,255,0.96),rgba(245,243,255,0.96))] p-4 shadow-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">New</p>
                <h3 className="mt-1 text-lg font-semibold text-slate-900">Suggest a future story</h3>
                <p className="mt-1 text-sm text-slate-600">
                  Share a brief outline, lesson, or bedtime scenario you want Buddybug to learn from for future editorial
                  guidance.
                </p>
              </div>
              <Link
                href="/story-suggestions"
                className="rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-3 text-sm font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
              >
                Open story suggestions
              </Link>
            </div>
          </div>
        ) : null}
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

      {!books.length ? (
        <EmptyState title={emptyStateTitle} description={emptyStateDescription} />
      ) : (
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
                <div className="text-sm text-slate-200">Save stories to your Buddybug library for quick access later.</div>
                <SaveBookButton
                  bookId={book.book_id}
                  token={token}
                  childProfileId={selectedChildProfile?.id}
                  initialItem={savedItemsByBookId[book.book_id] ?? null}
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
      )}
    </div>
  );
}
