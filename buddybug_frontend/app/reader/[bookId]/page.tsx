"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { BedtimePackSummaryCard } from "@/components/BedtimePackSummaryCard";
import { BedtimeModeBadge } from "@/components/BedtimeModeBadge";
import { OfflineUnavailableState } from "@/components/OfflineUnavailableState";
import { PreviewIllustrationReviewPanel } from "@/components/admin/PreviewIllustrationReviewPanel";
import { RecommendedBookCard } from "@/components/RecommendedBookCard";
import { ReaderPageView } from "@/components/ReaderPageView";
import { ReaderProgressBar } from "@/components/ReaderProgressBar";
import { SaveBookButton } from "@/components/SaveBookButton";
import { StoryAudioPlayer } from "@/components/StoryAudioPlayer";
import { StoryFeedbackForm } from "@/components/StoryFeedbackForm";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useConnectivity } from "@/context/ConnectivityContext";
import { useFeatureFlags } from "@/context/FeatureFlagsContext";
import { useLocale } from "@/context/LocaleContext";
import { useOnboarding } from "@/context/OnboardingContext";
import { useParentalControls } from "@/context/ParentalControlsContext";
import {
  trackAutoplayBlockedByParentalControls,
  trackBedtimeModeUsed,
  trackBookCompleted,
  trackBookOpened,
  trackMessageVariantClicked,
  trackMessageVariantExposed,
  trackOnboardingCompleted,
  trackOnboardingFirstStoryOpened,
  trackOfflineReaderOpened,
  trackPageViewed,
  trackPreviewWallUpgradeClicked,
  trackPreviewWallHit,
  trackRecommendationViewed,
  trackVoiceSelected,
} from "@/lib/analytics";
import { apiGet, apiPatch, apiPost, ApiError } from "@/lib/api";
import { getReaderIdentifier } from "@/lib/auth";
import { fetchSavedLibrary, markLibraryBookOpened } from "@/lib/library";
import { fetchMessageExperimentBundle } from "@/lib/message-experiments";
import { queueSyncAction } from "@/lib/offline-sync";
import { getOfflineBookPackage } from "@/lib/offline-storage";
import type {
  AvailableVoicesResponse,
  BedtimePackDetailResponse,
  BedtimePackItemRead,
  CheckoutSessionResponse,
  MessageExperimentSurfaceCopy,
  OfflineBookPackageRecord,
  LocalizedReaderBookDetail,
  NarrationVoiceRead,
  ReadAlongDetailResponse,
  ReadAlongJoinResponse,
  RecommendationsResponse,
  RecommendedBookScore,
  ReaderAccessResponse,
  ReaderNarrationResponse,
  ReadingProgressRead,
  UserLibraryItemRead,
} from "@/lib/types";

const GUEST_PREVIEW_ACCESS: ReaderAccessResponse = {
  book_id: 0,
  can_read_full_book: false,
  can_use_audio: false,
  preview_page_limit: 2,
  reason: "Guest preview only",
};

function buildOfflineBookDetail(record: OfflineBookPackageRecord): LocalizedReaderBookDetail {
  return {
    book_id: record.payload.book.book_id,
    title: record.payload.book.title,
    cover_image_url: record.payload.book.cover_image_url,
    age_band: record.payload.book.age_band,
    content_lane_key: record.payload.book.content_lane_key || null,
    language: record.payload.book.language,
    published: record.payload.book.published,
    publication_status: record.payload.book.publication_status,
    pages: record.payload.pages,
  };
}

function buildOfflineNarration(record: OfflineBookPackageRecord): ReaderNarrationResponse | null {
  const audio = record.payload.audio;
  if (!audio) {
    return null;
  }
  return {
    narration: {
      id: audio.narration_id,
      book_id: record.book_id,
      language: audio.language,
      narration_voice_id: 0,
      duration_seconds: audio.duration_seconds,
      is_active: true,
    },
    voice: {
      id: 0,
      key: audio.voice_key,
      display_name: audio.voice_display_name,
      language: audio.language,
      style: null,
      description: "Offline narration",
      is_premium: false,
    },
    segments: audio.segments.map((segment, index) => ({
      id: index + 1,
      narration_id: audio.narration_id,
      page_number: segment.page_number,
      audio_url: segment.audio_url,
      duration_seconds: segment.duration_seconds,
    })),
  };
}

function ReaderPageContent() {
  const params = useParams<{ bookId: string }>();
  const searchParams = useSearchParams();
  const { user, token, isAuthenticated, isEditor, isLoading: authLoading } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const { isOnline } = useConnectivity();
  const { isEnabled } = useFeatureFlags();
  const { state: onboardingState, shouldShowOnboarding, advanceOnboarding } = useOnboarding();
  const { resolvedControls } = useParentalControls();
  const { locale, t } = useLocale();
  const bookId = Number(params.bookId);
  const isPreviewMode = useMemo(() => searchParams.get("preview") === "1", [searchParams]);
  const requestedReadAlongSessionId = useMemo(() => {
    const rawValue = searchParams.get("readAlongSessionId");
    if (!rawValue) {
      return null;
    }
    const parsedValue = Number(rawValue);
    return Number.isFinite(parsedValue) ? parsedValue : null;
  }, [searchParams]);
  const [book, setBook] = useState<LocalizedReaderBookDetail | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [savedProgress, setSavedProgress] = useState<ReadingProgressRead | null>(null);
  const [narration, setNarration] = useState<ReaderNarrationResponse | null>(null);
  const [availableVoices, setAvailableVoices] = useState<NarrationVoiceRead[]>([]);
  const [selectedVoiceKey, setSelectedVoiceKey] = useState<string | null>(null);
  const [narrationMessage, setNarrationMessage] = useState<string | null>(null);
  const [readerAccess, setReaderAccess] = useState<ReaderAccessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readyToSync, setReadyToSync] = useState(false);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [upgradeError, setUpgradeError] = useState<string | null>(null);
  const [moreLikeThis, setMoreLikeThis] = useState<RecommendedBookScore[]>([]);
  const [libraryItem, setLibraryItem] = useState<UserLibraryItemRead | null>(null);
  const [usingOfflinePackage, setUsingOfflinePackage] = useState(false);
  const [previewWallTracked, setPreviewWallTracked] = useState(false);
  const [completionTracked, setCompletionTracked] = useState(false);
  const [onboardingStoryTracked, setOnboardingStoryTracked] = useState(false);
  const [previewWallCopy, setPreviewWallCopy] = useState<MessageExperimentSurfaceCopy | null>(null);
  const [previewRefreshKey, setPreviewRefreshKey] = useState(0);
  const [pinnedPreviewReviewPageNumber, setPinnedPreviewReviewPageNumber] = useState<number | null>(null);
  const [readAlongDetail, setReadAlongDetail] = useState<ReadAlongDetailResponse | null>(null);
  const [readAlongLoading, setReadAlongLoading] = useState(false);
  const [readAlongError, setReadAlongError] = useState<string | null>(null);
  const [readAlongActionLoading, setReadAlongActionLoading] = useState<"create" | "join" | "end" | null>(null);
  const lastReadAlongSyncRef = useRef<string | null>(null);
  const [bedtimePackDetail, setBedtimePackDetail] = useState<BedtimePackDetailResponse | null>(null);
  const bedtimePackOpenedRef = useRef<number | null>(null);
  const bedtimePackCompletedRef = useRef<number | null>(null);
  const lastViewedPreviewPageNumberRef = useRef(0);
  const pageRefs = useRef<Array<HTMLDivElement | null>>([]);
  const pendingScrollRef = useRef<{ index: number; behavior: ScrollBehavior } | null>(null);
  const lastHeaderScrollYRef = useRef(0);
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);

  const narratedStoriesEnabled = isEnabled("narrated_stories_enabled");
  const effectiveLanguage = selectedChildProfile?.language || locale;
  const authenticatedChildProfileId = isAuthenticated && token ? (selectedChildProfile?.id ?? undefined) : undefined;

  useEffect(() => {
    setOnboardingStoryTracked(false);
  }, [bookId]);

  useEffect(() => {
    if (isPreviewMode && book?.pages[currentIndex]) {
      lastViewedPreviewPageNumberRef.current = book.pages[currentIndex].page_number;
    }
  }, [book, currentIndex, isPreviewMode]);

  useEffect(() => {
    setPinnedPreviewReviewPageNumber(null);
  }, [bookId, previewRefreshKey]);

  useEffect(() => {
    void fetchMessageExperimentBundle({ token, user }).then((bundle) => setPreviewWallCopy(bundle.preview_wall));
  }, [token, user]);

  useEffect(() => {
    if (!bookId || authLoading) {
      return;
    }

    async function loadReaderState() {
      setLoading(true);
      setError(null);
      setReadyToSync(false);
      setPreviewWallTracked(false);
      setCompletionTracked(false);

      try {
        const cachedOfflinePackage = await getOfflineBookPackage(bookId, effectiveLanguage).catch(() => null);
        setUpgradeError(null);
        const authToken = isAuthenticated ? token : null;
        if (!isOnline) {
          if (!cachedOfflinePackage) {
            throw new Error("Offline copy not found for this story.");
          }
          const offlineBook = buildOfflineBookDetail(cachedOfflinePackage);
          setBook(offlineBook);
          setReaderAccess({
            book_id: offlineBook.book_id,
            can_read_full_book: true,
            can_use_audio: Boolean(cachedOfflinePackage.payload.audio),
            preview_page_limit: offlineBook.pages.length,
            reason: "Offline package loaded",
          });
          setNarration(buildOfflineNarration(cachedOfflinePackage));
          setAvailableVoices(
            cachedOfflinePackage.payload.audio
              ? [
                  {
                    id: 0,
                    key: cachedOfflinePackage.payload.audio.voice_key,
                    display_name: cachedOfflinePackage.payload.audio.voice_display_name,
                    language: cachedOfflinePackage.payload.audio.language,
                    style: null,
                    description: "Offline narration",
                    is_premium: false,
                  },
                ]
              : [],
          );
          setNarrationMessage(cachedOfflinePackage.payload.audio ? null : "Offline reading loaded. Audio is best-effort.");
          setCurrentIndex(0);
          setSavedProgress(null);
          setUsingOfflinePackage(true);
          if (isAuthenticated && authToken) {
            void queueSyncAction("library_opened", {
              book_id: bookId,
              child_profile_id: selectedChildProfile?.id ?? null,
            });
          }
          void trackOfflineReaderOpened(bookId, {
            token: authToken,
            user,
            language: effectiveLanguage,
            childProfileId: selectedChildProfile?.id,
            source: "offline_reader_load",
          });
          return;
        }
        const loadBookDetail = async () => {
          if (!isPreviewMode) {
            return apiGet<LocalizedReaderBookDetail>(`/reader/books/${bookId}`, {
              token: authToken,
              query: {
                language: effectiveLanguage,
                child_profile_id: authenticatedChildProfileId,
              },
            });
          }

          try {
            return await apiGet<LocalizedReaderBookDetail>(`/reader/books/${bookId}/preview`, {
              token: authToken,
              query: {
                language: effectiveLanguage,
              },
            });
          } catch (err) {
            // Fall back to the normal reader route so published books still open
            // even if the dedicated internal preview endpoint is unavailable.
            if (err instanceof ApiError && err.status === 404) {
              return apiGet<LocalizedReaderBookDetail>(`/reader/books/${bookId}`, {
                token: authToken,
                query: {
                  language: effectiveLanguage,
                  child_profile_id: authenticatedChildProfileId,
                },
              });
            }
            throw err;
          }
        };

        const [bookDetail, access] = await Promise.all([
          loadBookDetail(),
          isPreviewMode
            ? Promise.resolve({
                book_id: bookId,
                can_read_full_book: true,
                can_use_audio: false,
                preview_page_limit: Number.MAX_SAFE_INTEGER,
                reason: "Internal preview",
              })
            : isAuthenticated && authToken
              ? apiGet<ReaderAccessResponse>(`/subscriptions/me/access/books/${bookId}`, {
                  token: authToken,
                })
              : Promise.resolve({
                  ...GUEST_PREVIEW_ACCESS,
                  book_id: bookId,
                }),
        ]);
        setBook(bookDetail);
        setReaderAccess(access);
        setUsingOfflinePackage(false);
        void trackBookOpened(bookDetail.book_id, {
          token: authToken,
          user,
          language: effectiveLanguage,
          childProfileId: selectedChildProfile?.id,
          source: "reader_page_load",
        });

        const readerIdentifier = getReaderIdentifier(user);
        if (!isPreviewMode) {
          try {
            const progress = await apiGet<ReadingProgressRead>("/reader/progress", {
              token: authToken,
              query: {
                reader_identifier: readerIdentifier,
                book_id: bookId,
                child_profile_id: authenticatedChildProfileId,
              },
            });
            setSavedProgress(progress);
            const matchedIndex = bookDetail.pages.findIndex(
              (page) => page.page_number === progress.current_page_number,
            );
            const nextIndex = matchedIndex >= 0 ? matchedIndex : 0;
            setCurrentIndex(nextIndex);
            if (nextIndex > 0) {
              pendingScrollRef.current = { index: nextIndex, behavior: "auto" };
            }
          } catch (err) {
            if (!(err instanceof ApiError) || err.status !== 404) {
              throw err;
            }
            setSavedProgress(null);
            setCurrentIndex(0);
          }
        } else {
          setSavedProgress(null);
          const previousPreviewPageNumber = lastViewedPreviewPageNumberRef.current;
          const matchedIndex = bookDetail.pages.findIndex((page) => page.page_number === previousPreviewPageNumber);
          const nextIndex = matchedIndex >= 0 ? matchedIndex : 0;
          setCurrentIndex(nextIndex);
          if (nextIndex > 0) {
            pendingScrollRef.current = { index: nextIndex, behavior: "auto" };
          }
        }
        if (!isPreviewMode && isAuthenticated && authToken) {
          const [savedLibrary] = await Promise.all([
            fetchSavedLibrary({ token: authToken, childProfileId: authenticatedChildProfileId }),
          ]);
          setLibraryItem(savedLibrary.items.find((item) => item.book_id === bookId) ?? null);
          void markLibraryBookOpened(bookId, { token: authToken, childProfileId: authenticatedChildProfileId });
        } else {
          setLibraryItem(null);
        }
      } catch (err) {
        const cachedOfflinePackage = await getOfflineBookPackage(bookId, effectiveLanguage).catch(() => null);
        if (cachedOfflinePackage) {
          const offlineBook = buildOfflineBookDetail(cachedOfflinePackage);
          setBook(offlineBook);
          setReaderAccess({
            book_id: offlineBook.book_id,
            can_read_full_book: true,
            can_use_audio: Boolean(cachedOfflinePackage.payload.audio),
            preview_page_limit: offlineBook.pages.length,
            reason: "Offline package loaded",
          });
          setNarration(buildOfflineNarration(cachedOfflinePackage));
          setAvailableVoices(
            cachedOfflinePackage.payload.audio
              ? [
                  {
                    id: 0,
                    key: cachedOfflinePackage.payload.audio.voice_key,
                    display_name: cachedOfflinePackage.payload.audio.voice_display_name,
                    language: cachedOfflinePackage.payload.audio.language,
                    style: null,
                    description: "Offline narration",
                    is_premium: false,
                  },
                ]
              : [],
          );
          setNarrationMessage(cachedOfflinePackage.payload.audio ? null : "Offline reading loaded. Audio is best-effort.");
          setCurrentIndex(0);
          setSavedProgress(null);
          setUsingOfflinePackage(true);
          void trackOfflineReaderOpened(bookId, {
            token: isAuthenticated ? token : null,
            user,
            language: effectiveLanguage,
            childProfileId: selectedChildProfile?.id,
            source: "offline_reader_fallback",
          });
        } else {
          setError(err instanceof Error ? err.message : "Unable to load this book");
        }
      } finally {
        setLoading(false);
        setReadyToSync(true);
      }
    }

    void loadReaderState();
  }, [
    authLoading,
    bookId,
    effectiveLanguage,
    isAuthenticated,
    isOnline,
    isPreviewMode,
    previewRefreshKey,
    selectedChildProfile?.id,
    token,
    user,
  ]);

  useEffect(() => {
    if (
      !book ||
      loading ||
      !isAuthenticated ||
      onboardingStoryTracked ||
      !shouldShowOnboarding ||
      onboardingState?.current_step !== "first_story"
    ) {
      return;
    }

    setOnboardingStoryTracked(true);
    void advanceOnboarding({ first_story_opened: true })
      .then(() => {
        void trackOnboardingFirstStoryOpened(book.book_id, {
          token,
          user,
          language: effectiveLanguage,
          childProfileId: selectedChildProfile?.id,
          source: "reader_page_load",
        });
        void trackOnboardingCompleted({
          token,
          user,
          language: effectiveLanguage,
          childProfileId: selectedChildProfile?.id,
          source: "reader_page_load",
        });
      })
      .catch(() => {
        setOnboardingStoryTracked(false);
      });
  }, [
    advanceOnboarding,
    book,
    effectiveLanguage,
    isAuthenticated,
    loading,
    onboardingState?.current_step,
    onboardingStoryTracked,
    selectedChildProfile?.id,
    shouldShowOnboarding,
    token,
    user,
  ]);

  useEffect(() => {
    if (!bookId || authLoading || usingOfflinePackage || !isOnline) {
      return;
    }
    if (!narratedStoriesEnabled) {
      setNarration(null);
      setNarrationMessage(null);
      setAvailableVoices([]);
      return;
    }

    const authToken = isAuthenticated ? token : null;
    async function loadNarrationState() {
      try {
        const voicesResponse = await apiGet<AvailableVoicesResponse>("/narration/voices", {
          token: authToken,
          query: { language: effectiveLanguage, child_profile_id: authenticatedChildProfileId },
        });
        setAvailableVoices(voicesResponse.voices);

        const preferredVoiceKey =
          selectedVoiceKey && voicesResponse.voices.some((voice) => voice.key === selectedVoiceKey)
            ? selectedVoiceKey
            : undefined;
        try {
          const response = await apiGet<ReaderNarrationResponse>(`/narration/books/${bookId}`, {
            token: authToken,
            query: {
              language: effectiveLanguage,
              voice_key: preferredVoiceKey,
              child_profile_id: authenticatedChildProfileId,
            },
          });
          setNarration(response);
          setSelectedVoiceKey(response.voice.key);
          setNarrationMessage(null);
        } catch (err) {
          if (err instanceof ApiError && err.status === 403 && preferredVoiceKey) {
            const fallback = await apiGet<ReaderNarrationResponse>(`/narration/books/${bookId}`, {
              token: authToken,
              query: { language: effectiveLanguage, child_profile_id: authenticatedChildProfileId },
            });
            setNarration(fallback);
            setSelectedVoiceKey(fallback.voice.key);
            setNarrationMessage("That voice needs premium access. Switched to an available narration voice.");
            return;
          }
          throw err;
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setNarration(null);
          setNarrationMessage("Narrated version coming soon.");
          return;
        }
        if (err instanceof ApiError && err.status === 403) {
          setNarration(null);
          setNarrationMessage(err.message);
          return;
        }
        setNarration(null);
        setNarrationMessage("Narrated version coming soon.");
      }
    }

    void loadNarrationState();
  }, [authLoading, bookId, effectiveLanguage, isAuthenticated, isOnline, narratedStoriesEnabled, selectedChildProfile?.id, selectedVoiceKey, token, usingOfflinePackage]);

  useEffect(() => {
    if (!bookId || !isOnline) {
      setMoreLikeThis([]);
      return;
    }

    const authToken = isAuthenticated ? token : null;
    void apiGet<RecommendationsResponse>(`/recommendations/books/${bookId}/more-like-this`, {
      token: authToken,
      query: {
        user_context: isAuthenticated,
        child_profile_id: authenticatedChildProfileId,
        limit: 4,
      },
    })
      .then((response) => setMoreLikeThis(response.items.filter((item) => item.book_id !== bookId).slice(0, 4)))
      .catch(() => setMoreLikeThis([]));
  }, [bookId, isAuthenticated, isOnline, selectedChildProfile?.id, token]);

  useEffect(() => {
    if (!isAuthenticated || !token || !isOnline) {
      setBedtimePackDetail(null);
      bedtimePackOpenedRef.current = null;
      bedtimePackCompletedRef.current = null;
      return;
    }

    void apiGet<BedtimePackDetailResponse>("/bedtime-packs/me/latest", {
      token,
      query: { child_profile_id: authenticatedChildProfileId },
    })
      .then((response) => {
        setBedtimePackDetail(response);
        bedtimePackOpenedRef.current = null;
        bedtimePackCompletedRef.current = null;
      })
      .catch(() => {
        setBedtimePackDetail(null);
      });
  }, [isAuthenticated, isOnline, selectedChildProfile?.id, token]);

  const canReadFullBook = Boolean(readerAccess?.can_read_full_book);
  const previewLimit = readerAccess?.preview_page_limit ?? 2;
  const visiblePages = useMemo(() => {
    if (!book) {
      return [];
    }
    if (canReadFullBook || isPreviewMode || usingOfflinePackage) {
      return book.pages;
    }
    return book.pages.filter((page) => page.page_number <= previewLimit);
  }, [book, canReadFullBook, isPreviewMode, previewLimit, usingOfflinePackage]);
  const currentPage = useMemo(() => {
    if (!visiblePages.length) {
      return null;
    }
    return visiblePages[currentIndex] ?? null;
  }, [currentIndex, visiblePages]);
  const lastPageNumber = book?.pages[book.pages.length - 1]?.page_number ?? 0;
  const isAtStoryEnd = currentPage ? currentPage.page_number >= lastPageNumber : false;
  const isAtVisibleEnd = visiblePages.length > 0 ? currentIndex >= visiblePages.length - 1 : false;
  const usePagedPreviewReview = isPreviewMode && isEditor;
  const activeReadAlongDetail = readAlongDetail?.session.book_id === bookId ? readAlongDetail : null;
  const completed = Boolean(savedProgress?.completed || (canReadFullBook && isAtStoryEnd));
  const activeBedtimePackContext = useMemo(() => {
    if (!bedtimePackDetail) {
      return null;
    }
    const currentItemIndex = bedtimePackDetail.items.findIndex((item) => item.book_id === bookId);
    if (currentItemIndex < 0) {
      return null;
    }
    return {
      pack: bedtimePackDetail.pack,
      currentItem: bedtimePackDetail.items[currentItemIndex],
      currentItemIndex,
      nextItem: bedtimePackDetail.items[currentItemIndex + 1] || null,
    };
  }, [bedtimePackDetail, bookId]);
  const showPreviewUpsell = Boolean(
    readerAccess &&
      !readerAccess.can_read_full_book &&
      isAtVisibleEnd &&
      currentPage &&
      currentPage.page_number >= previewLimit,
  );

  function scrollToPageIndex(index: number, behavior: ScrollBehavior = "smooth") {
    if (!visiblePages.length) {
      return;
    }
    const clampedIndex = Math.max(0, Math.min(index, visiblePages.length - 1));
    setCurrentIndex(clampedIndex);
    const targetNode = pageRefs.current[clampedIndex];
    if (targetNode) {
      targetNode.scrollIntoView({ behavior, block: "start" });
      return;
    }
    pendingScrollRef.current = { index: clampedIndex, behavior };
  }

  function goToPreviewPage(index: number) {
    if (!visiblePages.length) {
      return;
    }
    const clampedIndex = Math.max(0, Math.min(index, visiblePages.length - 1));
    setPinnedPreviewReviewPageNumber(null);
    setCurrentIndex(clampedIndex);
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  useEffect(() => {
    if (!visiblePages.length) {
      return;
    }
    setCurrentIndex((existingIndex) => Math.min(existingIndex, visiblePages.length - 1));
  }, [visiblePages.length]);

  useEffect(() => {
    if (!visiblePages.length || !pendingScrollRef.current) {
      return;
    }
    const { index, behavior } = pendingScrollRef.current;
    const targetNode = pageRefs.current[index];
    if (!targetNode) {
      return;
    }
    targetNode.scrollIntoView({ behavior, block: "start" });
    pendingScrollRef.current = null;
  }, [currentIndex, visiblePages.length]);

  useEffect(() => {
    if (!visiblePages.length) {
      return;
    }
    let frameId = 0;

    const updateCurrentPageFromViewport = () => {
      frameId = 0;
      const anchor = Math.max(140, window.innerHeight * 0.28);
      let bestIndex = 0;
      let bestDistance = Number.POSITIVE_INFINITY;

      for (let index = 0; index < visiblePages.length; index += 1) {
        const node = pageRefs.current[index];
        if (!node) {
          continue;
        }
        const rect = node.getBoundingClientRect();
        const distance = Math.abs(rect.top - anchor);
        if (distance < bestDistance) {
          bestDistance = distance;
          bestIndex = index;
        }
      }

      setCurrentIndex((existingIndex) => (existingIndex === bestIndex ? existingIndex : bestIndex));
    };

    const scheduleViewportSync = () => {
      if (frameId) {
        return;
      }
      frameId = window.requestAnimationFrame(updateCurrentPageFromViewport);
    };

    scheduleViewportSync();
    window.addEventListener("scroll", scheduleViewportSync, { passive: true });
    window.addEventListener("resize", scheduleViewportSync);
    return () => {
      if (frameId) {
        window.cancelAnimationFrame(frameId);
      }
      window.removeEventListener("scroll", scheduleViewportSync);
      window.removeEventListener("resize", scheduleViewportSync);
    };
  }, [visiblePages]);

  useEffect(() => {
    lastHeaderScrollYRef.current = typeof window !== "undefined" ? window.scrollY : 0;
    setIsHeaderVisible(true);

    let frameId = 0;

    const updateHeaderVisibility = () => {
      frameId = 0;
      const currentScrollY = window.scrollY;
      const previousScrollY = lastHeaderScrollYRef.current;
      const delta = currentScrollY - previousScrollY;

      if (currentScrollY <= 24) {
        setIsHeaderVisible(true);
      } else if (delta > 10) {
        setIsHeaderVisible(false);
      } else if (delta < -8) {
        setIsHeaderVisible(true);
      }

      lastHeaderScrollYRef.current = currentScrollY;
    };

    const scheduleHeaderVisibility = () => {
      if (frameId) {
        return;
      }
      frameId = window.requestAnimationFrame(updateHeaderVisibility);
    };

    window.addEventListener("scroll", scheduleHeaderVisibility, { passive: true });
    return () => {
      if (frameId) {
        window.cancelAnimationFrame(frameId);
      }
      window.removeEventListener("scroll", scheduleHeaderVisibility);
    };
  }, [bookId, previewRefreshKey]);

  useEffect(() => {
    if (!readAlongDetail || readAlongDetail.session.book_id === bookId) {
      return;
    }
    setReadAlongDetail(null);
    setReadAlongError(null);
    lastReadAlongSyncRef.current = null;
  }, [bookId, readAlongDetail]);

  useEffect(() => {
    if (!book || !activeReadAlongDetail) {
      return;
    }
    const matchedIndex = book.pages.findIndex(
      (page) => page.page_number === activeReadAlongDetail.session.current_page_number,
    );
    if (matchedIndex >= 0) {
      scrollToPageIndex(matchedIndex);
    }
    lastReadAlongSyncRef.current = `${activeReadAlongDetail.session.current_page_number}:${activeReadAlongDetail.session.playback_state}`;
  }, [
    activeReadAlongDetail,
    book,
  ]);

  useEffect(() => {
    if (!requestedReadAlongSessionId || !isAuthenticated || !token) {
      return;
    }
    if (!isOnline) {
      setReadAlongError("Read-along needs a live connection.");
      return;
    }

    async function loadRequestedReadAlongSession() {
      setReadAlongLoading(true);
      setReadAlongError(null);
      try {
        const detail = await apiGet<ReadAlongDetailResponse>(`/read-along/sessions/${requestedReadAlongSessionId}`, { token });
        if (detail.session.book_id !== bookId) {
          setReadAlongDetail(null);
          setReadAlongError("This read-along code belongs to a different story. Open it from the Read Along page.");
          return;
        }
        setReadAlongDetail(detail);
      } catch (err) {
        setReadAlongError(err instanceof Error ? err.message : "Unable to load read-along session");
      } finally {
        setReadAlongLoading(false);
      }
    }

    void loadRequestedReadAlongSession();
  }, [bookId, isAuthenticated, isOnline, requestedReadAlongSessionId, token]);

  useEffect(() => {
    if (!activeReadAlongDetail || !token || !isOnline || activeReadAlongDetail.session.status !== "active") {
      return;
    }

    const intervalId = window.setInterval(() => {
      void apiGet<ReadAlongDetailResponse>(`/read-along/sessions/${activeReadAlongDetail.session.id}`, { token })
        .then((detail) => {
          if (detail.session.book_id === bookId) {
            setReadAlongDetail(detail);
          }
        })
        .catch(() => undefined);
    }, 4000);

    return () => window.clearInterval(intervalId);
  }, [activeReadAlongDetail, bookId, isOnline, token]);

  useEffect(() => {
    if (!book || !currentPage) {
      return;
    }
    void trackPageViewed(book.book_id, currentPage.page_number, {
      token: isAuthenticated ? token : null,
      user,
      language: effectiveLanguage,
      childProfileId: selectedChildProfile?.id,
    });
  }, [book, currentPage, effectiveLanguage, isAuthenticated, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    if (!showPreviewUpsell || !book || previewWallTracked) {
      return;
    }
    void trackPreviewWallHit(book.book_id, {
      token: isAuthenticated ? token : null,
      user,
      language: effectiveLanguage,
      childProfileId: selectedChildProfile?.id,
    });
    void trackMessageVariantExposed("preview_wall", {
      token: isAuthenticated ? token : null,
      user,
      language: effectiveLanguage,
      childProfileId: selectedChildProfile?.id,
      experimentKey: previewWallCopy?.experiment_key,
      experimentVariant: previewWallCopy?.variant,
      source: "reader_preview_wall",
    });
    setPreviewWallTracked(true);
  }, [
    book,
    effectiveLanguage,
    isAuthenticated,
    previewWallCopy?.experiment_key,
    previewWallCopy?.variant,
    previewWallTracked,
    selectedChildProfile?.id,
    showPreviewUpsell,
    token,
    user,
  ]);

  useEffect(() => {
    if (!book || !canReadFullBook || !isAtStoryEnd || completionTracked) {
      return;
    }
    void trackBookCompleted(book.book_id, {
      token: isAuthenticated ? token : null,
      user,
      language: effectiveLanguage,
      childProfileId: selectedChildProfile?.id,
      source: "reader_final_page",
    });
    setCompletionTracked(true);
  }, [book, canReadFullBook, completionTracked, effectiveLanguage, isAtStoryEnd, isAuthenticated, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    if (!moreLikeThis.length) {
      return;
    }
    void trackRecommendationViewed(
      moreLikeThis.map((item) => item.book_id),
      {
        token: isAuthenticated ? token : null,
        user,
        language: effectiveLanguage,
        childProfileId: selectedChildProfile?.id,
        source: "reader_more_like_this",
      },
    );
  }, [effectiveLanguage, isAuthenticated, moreLikeThis, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    if (!book || !resolvedControls?.bedtime_mode_enabled) {
      return;
    }
    void trackBedtimeModeUsed(book.book_id, {
      token: isAuthenticated ? token : null,
      user,
      language: effectiveLanguage,
      childProfileId: selectedChildProfile?.id,
      source: "reader_page",
    });
  }, [book, effectiveLanguage, isAuthenticated, resolvedControls?.bedtime_mode_enabled, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    if (!book || !resolvedControls || resolvedControls.allow_audio_autoplay) {
      return;
    }
    void trackAutoplayBlockedByParentalControls(book.book_id, {
      token: isAuthenticated ? token : null,
      user,
      language: effectiveLanguage,
      childProfileId: selectedChildProfile?.id,
    });
  }, [book, effectiveLanguage, isAuthenticated, resolvedControls, selectedChildProfile?.id, token, user]);

  useEffect(() => {
    const currentItem = activeBedtimePackContext?.currentItem;
    if (!currentItem || !token || !isOnline) {
      return;
    }
    if (currentItem.completion_status !== "pending" || bedtimePackOpenedRef.current === currentItem.id) {
      return;
    }
    bedtimePackOpenedRef.current = currentItem.id;
    void apiPatch<BedtimePackItemRead>(
      `/bedtime-packs/me/${activeBedtimePackContext.pack.id}/items/${currentItem.id}`,
      { completion_status: "opened" },
      { token },
    )
      .then((updatedItem) => {
        setBedtimePackDetail((current) =>
          current
            ? {
                ...current,
                items: current.items.map((item) => (item.id === updatedItem.id ? updatedItem : item)),
              }
            : current,
        );
      })
      .catch(() => {
        bedtimePackOpenedRef.current = null;
      });
  }, [activeBedtimePackContext, isOnline, token]);

  useEffect(() => {
    const currentItem = activeBedtimePackContext?.currentItem;
    if (!currentItem || !token || !isOnline || !completed) {
      return;
    }
    if (currentItem.completion_status === "completed" || bedtimePackCompletedRef.current === currentItem.id) {
      return;
    }
    bedtimePackCompletedRef.current = currentItem.id;
    void apiPatch<BedtimePackItemRead>(
      `/bedtime-packs/me/${activeBedtimePackContext.pack.id}/items/${currentItem.id}`,
      { completion_status: "completed" },
      { token },
    )
      .then((updatedItem) => {
        setBedtimePackDetail((current) =>
          current
            ? {
                ...current,
                items: current.items.map((item) => (item.id === updatedItem.id ? updatedItem : item)),
              }
            : current,
        );
      })
      .catch(() => {
        bedtimePackCompletedRef.current = null;
      });
  }, [activeBedtimePackContext, completed, isOnline, token]);

  useEffect(() => {
    if (!book || !currentPage || !token || !isOnline || !activeReadAlongDetail) {
      return;
    }
    if (activeReadAlongDetail.session.status !== "active") {
      return;
    }
    if (currentPage.page_number === activeReadAlongDetail.session.current_page_number) {
      lastReadAlongSyncRef.current = `${activeReadAlongDetail.session.current_page_number}:${activeReadAlongDetail.session.playback_state}`;
      return;
    }

    const nextPlaybackState = currentPage.page_number >= lastPageNumber ? "finished" : "reading";
    const nextSyncKey = `${currentPage.page_number}:${nextPlaybackState}`;
    if (lastReadAlongSyncRef.current === nextSyncKey) {
      return;
    }
    lastReadAlongSyncRef.current = nextSyncKey;

    void apiPatch<ReadAlongDetailResponse["session"]>(
      `/read-along/sessions/${activeReadAlongDetail.session.id}`,
      {
        current_page_number: currentPage.page_number,
        playback_state: nextPlaybackState,
      },
      { token },
    )
      .then((updatedSession) => {
        setReadAlongDetail((current) => (current ? { ...current, session: updatedSession } : current));
      })
      .catch(() => {
        lastReadAlongSyncRef.current = null;
      });
  }, [activeReadAlongDetail, book, currentPage, isOnline, lastPageNumber, token]);

  useEffect(() => {
    if (!readyToSync || !book || !currentPage || authLoading) {
      return;
    }

    const authToken = isAuthenticated ? token : null;
    const readerIdentifier = getReaderIdentifier(user);
    const payload = {
      reader_identifier: readerIdentifier,
      book_id: book.book_id,
      child_profile_id: authenticatedChildProfileId,
      current_page_number: currentPage.page_number,
      completed: canReadFullBook && currentPage.page_number >= lastPageNumber,
    };

    if (!isOnline) {
      void queueSyncAction("reading_progress", payload);
      return;
    }

    void apiPost<ReadingProgressRead>("/reader/progress", payload, { token: authToken })
      .then((progress) => setSavedProgress(progress))
      .catch(() => undefined);
  }, [authLoading, authenticatedChildProfileId, book, canReadFullBook, currentPage, isAuthenticated, isOnline, lastPageNumber, readyToSync, token, user]);

  function handleMarkFinished() {
    if (!book || !currentPage) {
      return;
    }
    const authToken = isAuthenticated ? token : null;
    const readerIdentifier = getReaderIdentifier(user);
    const payload = {
      reader_identifier: readerIdentifier,
      book_id: book.book_id,
      child_profile_id: authenticatedChildProfileId,
      current_page_number: lastPageNumber,
      completed: canReadFullBook,
    };
    if (!isOnline) {
      void queueSyncAction("reading_progress", payload);
      return;
    }
    void apiPost<ReadingProgressRead>("/reader/progress", payload, { token: authToken })
      .then((progress) => setSavedProgress(progress))
      .catch(() => undefined);
  }

  async function handleUpgradeToPremium() {
    if (!token) {
      return;
    }

    setUpgradeLoading(true);
    setUpgradeError(null);
    try {
      const response = await apiPost<CheckoutSessionResponse>(
        "/billing/checkout",
        { price_key: "premium_monthly" },
        { token },
      );
      window.location.assign(response.checkout_url);
    } catch (err) {
      setUpgradeError(err instanceof Error ? err.message : "Unable to open checkout");
      setUpgradeLoading(false);
    }
  }

  async function handleCreateReadAlongSession() {
    if (!token || !book || !currentPage || !isOnline) {
      return;
    }

    setReadAlongActionLoading("create");
    setReadAlongError(null);
    try {
      const detail = await apiPost<ReadAlongDetailResponse>(
        "/read-along/sessions",
        {
          book_id: book.book_id,
          child_profile_id: authenticatedChildProfileId,
          language: effectiveLanguage,
          current_page_number: currentPage.page_number,
          playback_state: "paused",
        },
        { token },
      );
      setReadAlongDetail(detail);
      lastReadAlongSyncRef.current = `${detail.session.current_page_number}:${detail.session.playback_state}`;
    } catch (err) {
      setReadAlongError(err instanceof Error ? err.message : "Unable to create read-along session");
    } finally {
      setReadAlongActionLoading(null);
    }
  }

  async function handleJoinReadAlongSession(joinCode: string) {
    if (!token || !isOnline) {
      return;
    }

    setReadAlongActionLoading("join");
    setReadAlongError(null);
    try {
      const joinResponse = await apiPost<ReadAlongJoinResponse>(
        "/read-along/join",
        {
          join_code: joinCode,
          child_profile_id: authenticatedChildProfileId,
        },
        { token },
      );
      if (joinResponse.session.book_id !== bookId) {
        setReadAlongError("That code belongs to a different story. Open it from the Read Along page instead.");
        setReadAlongDetail(null);
        return;
      }
      const detail = await apiGet<ReadAlongDetailResponse>(`/read-along/sessions/${joinResponse.session.id}`, { token });
      setReadAlongDetail(detail);
      lastReadAlongSyncRef.current = `${detail.session.current_page_number}:${detail.session.playback_state}`;
    } catch (err) {
      setReadAlongError(err instanceof Error ? err.message : "Unable to join read-along session");
    } finally {
      setReadAlongActionLoading(null);
    }
  }

  async function handleEndReadAlongSession() {
    if (!token || !activeReadAlongDetail) {
      return;
    }

    setReadAlongActionLoading("end");
    setReadAlongError(null);
    try {
      const endedSession = await apiPost<ReadAlongDetailResponse["session"]>(
        `/read-along/sessions/${activeReadAlongDetail.session.id}/end`,
        undefined,
        { token },
      );
      setReadAlongDetail((current) => (current ? { ...current, session: endedSession } : current));
      lastReadAlongSyncRef.current = `${endedSession.current_page_number}:${endedSession.playback_state}`;
    } catch (err) {
      setReadAlongError(err instanceof Error ? err.message : "Unable to end read-along session");
    } finally {
      setReadAlongActionLoading(null);
    }
  }

  if (authLoading || loading) {
    return <LoadingState message="Opening your story..." />;
  }

  if ((error || !book || !currentPage) && !isOnline) {
    return <OfflineUnavailableState description={error || "This story has not been saved on this device yet."} />;
  }

  if (error || !book || !currentPage) {
    return <EmptyState title="Unable to open book" description={error || "This story could not be loaded."} />;
  }

  return (
    <div className="space-y-4">
      <section className="space-y-4">
        <header
          className={`sticky top-2 z-20 rounded-[1.75rem] border border-white/70 bg-white/88 px-4 py-3 shadow-sm backdrop-blur transition duration-200 ${
            isHeaderVisible ? "translate-y-0 opacity-100" : "-translate-y-[calc(100%+0.75rem)] opacity-0"
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Link
              href={isPreviewMode ? "/admin/workflow" : "/library"}
              className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-900 shadow-sm"
            >
              {isPreviewMode ? "Back to workflow" : t("backToLibrary")}
            </Link>
            <p className="text-sm font-medium text-slate-600">
              {currentPage.page_number} / {lastPageNumber}
            </p>
          </div>

          <div className="mt-3 min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("readerLabel")}</p>
            <h2 className="mt-1 text-lg font-semibold text-slate-900 sm:text-xl">{book.title}</h2>
            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[13px] sm:text-sm">
              {readerAccess ? (
                <span className="text-slate-600">
                  {usingOfflinePackage
                    ? "Reading from a copy already saved on this device."
                    : readerAccess.can_read_full_book
                      ? t("premiumAccessUnlocked")
                      : t("freePreviewMessage")}
                </span>
              ) : null}
              {selectedChildProfile ? (
                <span className="text-indigo-700">
                  Reading for {selectedChildProfile.display_name} in {selectedChildProfile.language.toUpperCase()}
                </span>
              ) : null}
            </div>
          </div>

          <div className="mt-2.5 flex flex-wrap items-center gap-2">
            <BedtimeModeBadge active={Boolean(resolvedControls?.bedtime_mode_enabled)} />
          </div>

          <div className="mt-2.5">
            <ReaderProgressBar currentPageNumber={currentPage.page_number} totalPageNumber={lastPageNumber} />
          </div>
        </header>

        {usePagedPreviewReview ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-[1.5rem] border border-indigo-100 bg-indigo-50/70 px-4 py-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">Editorial preview</p>
                <p className="mt-1 text-sm text-slate-600">Review one page at a time, then move to the next page.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={currentIndex <= 0}
                  onClick={() => goToPreviewPage(currentIndex - 1)}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900 disabled:opacity-50"
                >
                  Previous page
                </button>
                <button
                  type="button"
                  disabled={currentIndex >= visiblePages.length - 1}
                  onClick={() => goToPreviewPage(currentIndex + 1)}
                  className="rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-2 text-sm font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)] disabled:opacity-50"
                >
                  Next page
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <div className="px-1">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {currentPage.page_number === 0 ? "Cover" : `Page ${currentPage.page_number} of ${lastPageNumber}`}
                </p>
              </div>
              <div className="rounded-[2.25rem] ring-2 ring-indigo-200/80 ring-offset-2 ring-offset-transparent">
                <ReaderPageView book={book} page={currentPage} />
              </div>
              {currentPage.page_number > 0 ? (
                <PreviewIllustrationReviewPanel
                  page={currentPage}
                  pageIndex={currentIndex}
                  bookId={book.book_id}
                  storyDraftId={book.story_draft_id ?? null}
                  pageMapping={book.page_mapping ?? null}
                  token={token}
                  onActiveReviewChange={(active) => {
                    setPinnedPreviewReviewPageNumber(active ? currentPage.page_number : null);
                  }}
                  onPreviewUpdated={async () => {
                    setPreviewRefreshKey((current) => current + 1);
                  }}
                />
              ) : null}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {visiblePages.map((page, index) => (
              <div
                key={`reader-page-${page.page_number}-${previewRefreshKey}`}
                ref={(node) => {
                  pageRefs.current[index] = node;
                }}
                className="scroll-mt-32 space-y-3"
              >
                <div className="px-1">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {page.page_number === 0 ? "Cover" : `Page ${page.page_number} of ${lastPageNumber}`}
                  </p>
                </div>
                <div className={index === currentIndex ? "rounded-[2.25rem] ring-2 ring-indigo-200/80 ring-offset-2 ring-offset-transparent" : ""}>
                  <ReaderPageView book={book} page={page} />
                </div>
                {isPreviewMode &&
                isEditor &&
                page.page_number > 0 &&
                (index === currentIndex || pinnedPreviewReviewPageNumber === page.page_number) ? (
                  <PreviewIllustrationReviewPanel
                    page={page}
                    pageIndex={index}
                    bookId={book.book_id}
                    storyDraftId={book.story_draft_id ?? null}
                    pageMapping={book.page_mapping ?? null}
                    token={token}
                    onActiveReviewChange={(active) => {
                      setPinnedPreviewReviewPageNumber((current) => {
                        if (active) {
                          return page.page_number;
                        }
                        return current === page.page_number ? null : current;
                      });
                    }}
                    onPreviewUpdated={async () => {
                      setPreviewRefreshKey((current) => current + 1);
                    }}
                  />
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>

      {narratedStoriesEnabled ? (
        narration ? (
          <StoryAudioPlayer
            bookId={book.book_id}
            narration={narration}
            voices={availableVoices}
            currentPageNumber={currentPage.page_number}
            onPageChange={(pageNumber) => {
              const matchedIndex = visiblePages.findIndex((page) => page.page_number === pageNumber);
              if (matchedIndex >= 0) {
                scrollToPageIndex(matchedIndex);
              }
            }}
            onVoiceChange={(voiceKey) => {
              setSelectedVoiceKey(voiceKey);
              void trackVoiceSelected(book.book_id, voiceKey, {
                token: isAuthenticated ? token : null,
                user,
                language: effectiveLanguage,
                childProfileId: selectedChildProfile?.id,
              });
            }}
            token={token}
            user={user}
            language={effectiveLanguage}
            childProfileId={selectedChildProfile?.id}
            resolvedControls={resolvedControls}
          />
        ) : (
          <section className="rounded-[2rem] border border-dashed border-slate-300 bg-white/70 p-4 text-sm text-slate-600">
            {narrationMessage || "Narrated version coming soon."}
          </section>
        )
      ) : null}

      <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Save to your library</h3>
          <p className="mt-1 text-sm text-slate-600">
            Keep this story in your Buddybug account so it is easy to find again later.
          </p>
        </div>

        {isAuthenticated ? (
          <div className="space-y-3 rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4">
            <SaveBookButton
              bookId={book.book_id}
              token={token}
              childProfileId={selectedChildProfile?.id}
              initialItem={libraryItem}
              onChanged={setLibraryItem}
            />
            <p className="text-sm text-slate-600">
              Saved stories stay in your Buddybug library so you can reopen them quickly whenever you sign in.
            </p>
          </div>
        ) : (
          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4">
            <p className="text-sm text-slate-600">
              Sign in to save stories to your Buddybug library.
            </p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <Link
                href="/login"
                className="min-h-12 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="min-h-12 rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-3 text-center font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
              >
                Create account
              </Link>
            </div>
          </div>
        )}
      </section>

      {activeBedtimePackContext ? (
        <section className="space-y-3 rounded-[2rem] border border-indigo-100 bg-indigo-50/80 p-5 shadow-sm">
          <div>
            <p className="text-sm font-medium text-indigo-700">Part of tonight's pack</p>
            <h3 className="mt-1 text-xl font-semibold text-slate-900">{activeBedtimePackContext.pack.title}</h3>
            <p className="mt-1 text-sm text-slate-600">
              Story {activeBedtimePackContext.currentItem.position} of {bedtimePackDetail?.items.length || 0}
              {activeBedtimePackContext.currentItem.recommended_narration ? " • Narration recommended here" : ""}
            </p>
          </div>
          <BedtimePackSummaryCard detail={bedtimePackDetail} />
        </section>
      ) : null}

      {showPreviewUpsell ? (
        <section className="space-y-2 rounded-[2rem] border border-amber-200 bg-amber-50/90 p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">{previewWallCopy?.title || t("previewEndTitle")}</h3>
          <p className="text-sm text-slate-700">{previewWallCopy?.description || t("previewEndDescription")}</p>
          {upgradeError ? <p className="text-sm text-rose-700">{upgradeError}</p> : null}
          {isAuthenticated ? (
            <button
              type="button"
              onClick={() => {
                void trackMessageVariantClicked("preview_wall", {
                  token: isAuthenticated ? token : null,
                  user,
                  language: effectiveLanguage,
                  childProfileId: selectedChildProfile?.id,
                  experimentKey: previewWallCopy?.experiment_key,
                  experimentVariant: previewWallCopy?.variant,
                  source: "reader_preview_wall",
                  target: "/profile",
                });
                void trackPreviewWallUpgradeClicked({
                  token: isAuthenticated ? token : null,
                  user,
                  language: effectiveLanguage,
                  childProfileId: selectedChildProfile?.id,
                  experimentKey: previewWallCopy?.experiment_key,
                  experimentVariant: previewWallCopy?.variant,
                  source: "reader_preview_wall",
                });
                void handleUpgradeToPremium();
              }}
              disabled={upgradeLoading}
              className="w-full rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-3 font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)] disabled:opacity-60"
            >
              {upgradeLoading ? t("openingCheckout") : previewWallCopy?.primary_cta_label || t("upgradeToPremium")}
            </button>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              <Link
                href="/login"
                onClick={() => {
                  void trackMessageVariantClicked("preview_wall", {
                    user,
                    language: effectiveLanguage,
                    childProfileId: selectedChildProfile?.id,
                    experimentKey: previewWallCopy?.experiment_key,
                    experimentVariant: previewWallCopy?.variant,
                    source: "reader_preview_wall_guest",
                    target: "/login",
                  });
                }}
                className="rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-3 text-center font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
              >
                {previewWallCopy?.guest_primary_label || t("loginToUpgrade")}
              </Link>
              <Link
                href="/register"
                onClick={() => {
                  void trackMessageVariantClicked("preview_wall", {
                    user,
                    language: effectiveLanguage,
                    childProfileId: selectedChildProfile?.id,
                    experimentKey: previewWallCopy?.experiment_key,
                    experimentVariant: previewWallCopy?.variant,
                    source: "reader_preview_wall_guest",
                    target: "/register",
                  });
                }}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
              >
                {previewWallCopy?.guest_secondary_label || t("createAccount")}
              </Link>
            </div>
          )}
        </section>
      ) : null}

      {(isAtStoryEnd || completed) && canReadFullBook && (
        <StoryFeedbackForm
          bookId={book.book_id}
          token={isAuthenticated ? token : null}
          canSubmit={isAuthenticated}
          childProfileId={selectedChildProfile?.id ?? null}
          completed={true}
        />
      )}

      {(isAtStoryEnd || completed) && moreLikeThis.length ? (
        <section className="space-y-3">
          <h3 className="text-xl font-semibold text-slate-900">{t("moreLikeThis")}</h3>
          <div className="grid gap-3">
            {moreLikeThis.map((item) => (
              <RecommendedBookCard
                key={`more-like-this-${item.book_id}`}
                item={item}
                reasonPrefix={t("recommendationReasonPrefix")}
                analyticsSource="reader_more_like_this"
                token={token}
                user={user}
              />
            ))}
          </div>
        </section>
      ) : null}

      {(isAtStoryEnd || completed) && activeBedtimePackContext?.nextItem ? (
        <section className="space-y-3 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
          <h3 className="text-xl font-semibold text-slate-900">Next in tonight's pack</h3>
          <p className="text-sm text-slate-600">
            Keep the bedtime rhythm going with story {activeBedtimePackContext.nextItem.position}.
          </p>
          <Link
            href={`/reader/${activeBedtimePackContext.nextItem.book_id}`}
            className="inline-flex rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-3 text-sm font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
          >
            Open next story
          </Link>
        </section>
      ) : null}

    </div>
  );
}

export default function ReaderPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <ReaderPageContent />
    </Suspense>
  );
}
