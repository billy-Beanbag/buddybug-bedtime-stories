"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { BedtimePackSummaryCard } from "@/components/BedtimePackSummaryCard";
import { BedtimeModeBadge } from "@/components/BedtimeModeBadge";
import { OfflineBookBadge } from "@/components/OfflineBookBadge";
import { OfflineUnavailableState } from "@/components/OfflineUnavailableState";
import { PreviewIllustrationReviewPanel } from "@/components/admin/PreviewIllustrationReviewPanel";
import { RecommendedBookCard } from "@/components/RecommendedBookCard";
import { ReaderControls } from "@/components/ReaderControls";
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
  trackOfflineBookSaved,
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
import { downloadBookPackageForOffline, fetchDownloadAccess, fetchSavedLibrary, markLibraryBookOpened } from "@/lib/library";
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
  ReaderDownloadAccessResponse,
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
  const [downloadAccess, setDownloadAccess] = useState<ReaderDownloadAccessResponse | null>(null);
  const [offlinePackage, setOfflinePackage] = useState<OfflineBookPackageRecord | null>(null);
  const [usingOfflinePackage, setUsingOfflinePackage] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [previewWallTracked, setPreviewWallTracked] = useState(false);
  const [completionTracked, setCompletionTracked] = useState(false);
  const [onboardingStoryTracked, setOnboardingStoryTracked] = useState(false);
  const [previewWallCopy, setPreviewWallCopy] = useState<MessageExperimentSurfaceCopy | null>(null);
  const [previewRefreshKey, setPreviewRefreshKey] = useState(0);
  const [readAlongDetail, setReadAlongDetail] = useState<ReadAlongDetailResponse | null>(null);
  const [readAlongLoading, setReadAlongLoading] = useState(false);
  const [readAlongError, setReadAlongError] = useState<string | null>(null);
  const [readAlongActionLoading, setReadAlongActionLoading] = useState<"create" | "join" | "end" | null>(null);
  const lastReadAlongSyncRef = useRef<string | null>(null);
  const [bedtimePackDetail, setBedtimePackDetail] = useState<BedtimePackDetailResponse | null>(null);
  const bedtimePackOpenedRef = useRef<number | null>(null);
  const bedtimePackCompletedRef = useRef<number | null>(null);
  const lastViewedPreviewPageNumberRef = useRef(0);

  const narratedStoriesEnabled = isEnabled("narrated_stories_enabled");
  const offlineDownloadsEnabled = isEnabled("offline_downloads_enabled");
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
        setOfflinePackage(cachedOfflinePackage);
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
        setDownloadError(null);
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
            setCurrentIndex(matchedIndex >= 0 ? matchedIndex : 0);
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
          setCurrentIndex(matchedIndex >= 0 ? matchedIndex : 0);
        }
        if (!isPreviewMode && isAuthenticated && authToken) {
          const [savedLibrary, accessResponse] = await Promise.all([
            fetchSavedLibrary({ token: authToken, childProfileId: authenticatedChildProfileId }),
            fetchDownloadAccess(bookId, { token: authToken, language: effectiveLanguage }),
          ]);
          setLibraryItem(savedLibrary.items.find((item) => item.book_id === bookId) ?? null);
          setDownloadAccess(accessResponse);
          void markLibraryBookOpened(bookId, { token: authToken, childProfileId: authenticatedChildProfileId });
        } else {
          setLibraryItem(null);
          setDownloadAccess(null);
        }
      } catch (err) {
        const cachedOfflinePackage = await getOfflineBookPackage(bookId, effectiveLanguage).catch(() => null);
        if (cachedOfflinePackage) {
          const offlineBook = buildOfflineBookDetail(cachedOfflinePackage);
          setOfflinePackage(cachedOfflinePackage);
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

  const currentPage = useMemo(() => {
    if (!book) {
      return null;
    }
    return book.pages[currentIndex] ?? null;
  }, [book, currentIndex]);

  const lastPageNumber = book?.pages[book.pages.length - 1]?.page_number ?? 0;
  const isLastPage = currentPage ? currentPage.page_number >= lastPageNumber : false;
  const activeReadAlongDetail = readAlongDetail?.session.book_id === bookId ? readAlongDetail : null;
  const canReadFullBook = Boolean(readerAccess?.can_read_full_book);
  const previewLimit = readerAccess?.preview_page_limit ?? 2;
  const completed = Boolean(savedProgress?.completed || (canReadFullBook && isLastPage));
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
      isLastPage &&
      currentPage &&
      currentPage.page_number >= previewLimit,
  );

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
      setCurrentIndex((existingIndex) => (existingIndex === matchedIndex ? existingIndex : matchedIndex));
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
    if (!book || !canReadFullBook || !isLastPage || completionTracked) {
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
  }, [book, canReadFullBook, completionTracked, effectiveLanguage, isAuthenticated, isLastPage, selectedChildProfile?.id, token, user]);

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

  async function handleDownloadPackage() {
    if (!token || !book) {
      return;
    }
    setDownloadLoading(true);
    setDownloadError(null);
    try {
      const { packageRecord, offlineRecord } = await downloadBookPackageForOffline(book.book_id, {
        token,
        language: effectiveLanguage,
        childProfileId: authenticatedChildProfileId,
      });
      setOfflinePackage(offlineRecord);
      setUsingOfflinePackage(false);
      setDownloadAccess({
        book_id: book.book_id,
        can_download_full_book: true,
        package_available: true,
        package_url: packageRecord.package_url,
        reason: "Premium download available",
      });
      setLibraryItem((current) =>
        current
          ? {
              ...current,
              saved_for_offline: true,
              downloaded_at: new Date().toISOString(),
            }
          : current,
      );
      void trackOfflineBookSaved(book.book_id, {
        token,
        user,
        language: effectiveLanguage,
        childProfileId: selectedChildProfile?.id,
        source: "reader_page",
        packageVersion: packageRecord.package_version,
      });
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : "Unable to download this book");
    } finally {
      setDownloadLoading(false);
    }
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
      <section className="grid gap-4 md:min-h-[calc(100vh-2rem)] md:grid-rows-[auto_minmax(0,1fr)_auto]">
        <header className="rounded-[2rem] border border-white/70 bg-white/88 p-4 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("readerLabel")}</p>
              <h2 className="mt-1 text-xl font-semibold text-slate-900 sm:text-2xl">{book.title}</h2>
              {readerAccess ? (
                <p className="mt-1 text-sm text-slate-600">
                  {usingOfflinePackage
                    ? "Reading from your offline copy on this device."
                    : readerAccess.can_read_full_book
                      ? t("premiumAccessUnlocked")
                      : t("freePreviewMessage")}
                </p>
              ) : null}
              {selectedChildProfile ? (
                <p className="mt-1 text-sm text-indigo-700">
                  Reading for {selectedChildProfile.display_name} in {selectedChildProfile.language.toUpperCase()}
                </p>
              ) : null}
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <BedtimeModeBadge active={Boolean(resolvedControls?.bedtime_mode_enabled)} />
            <OfflineBookBadge
              availableOffline={Boolean(offlinePackage)}
              savedForOffline={Boolean(libraryItem?.saved_for_offline)}
              downloadedAt={libraryItem?.downloaded_at || offlinePackage?.saved_at || null}
            />
          </div>

          <div className="mt-3">
            <ReaderProgressBar currentPageNumber={currentPage.page_number} totalPageNumber={lastPageNumber} />
          </div>
        </header>

        <ReaderPageView book={book} page={currentPage} />

        {isPreviewMode && isEditor && currentPage.page_number > 0 ? (
          <PreviewIllustrationReviewPanel
            page={currentPage}
            pageIndex={currentIndex}
            bookId={book.book_id}
            storyDraftId={book.story_draft_id ?? null}
            pageMapping={book.page_mapping ?? null}
            token={token}
            onPreviewUpdated={async () => {
              setPreviewRefreshKey((current) => current + 1);
            }}
          />
        ) : null}

        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_220px] sm:items-start">
          <ReaderControls
            currentPageNumber={currentPage.page_number}
            totalPageNumber={lastPageNumber}
            canGoPrevious={currentIndex > 0}
            canGoNext={currentIndex < book.pages.length - 1}
            isLastPage={isLastPage}
            onPrevious={() => setCurrentIndex((index) => Math.max(index - 1, 0))}
            onNext={() => setCurrentIndex((index) => Math.min(index + 1, book.pages.length - 1))}
            onMarkFinished={canReadFullBook ? handleMarkFinished : undefined}
          />
          <Link
            href={isPreviewMode ? "/admin/workflow" : "/library"}
            className="inline-flex min-h-12 items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900 shadow-sm"
          >
            {isPreviewMode ? "Back to workflow" : t("backToLibrary")}
          </Link>
        </div>
      </section>

      {narratedStoriesEnabled ? (
        narration ? (
          <StoryAudioPlayer
            bookId={book.book_id}
            narration={narration}
            voices={availableVoices}
            currentPageNumber={currentPage.page_number}
            onPageChange={(pageNumber) => {
              const matchedIndex = book.pages.findIndex((page) => page.page_number === pageNumber);
              if (matchedIndex >= 0) {
                setCurrentIndex(matchedIndex);
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

      <details className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <summary className="cursor-pointer list-none text-lg font-semibold text-slate-900">
          Reader options
        </summary>
        <p className="mt-2 text-sm text-slate-600">
          Open this when you want downloads or saved-story options.
        </p>

        <div className="mt-4 space-y-4">
          {isAuthenticated ? (
            <section className="space-y-3 rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4">
              <h3 className="text-base font-semibold text-slate-900">Reader options</h3>
              <SaveBookButton
                bookId={book.book_id}
                token={token}
                childProfileId={selectedChildProfile?.id}
                language={book.language}
                initialItem={libraryItem}
                canSaveOffline={offlineDownloadsEnabled && Boolean(downloadAccess?.can_download_full_book)}
                onChanged={setLibraryItem}
              />
              {offlineDownloadsEnabled && downloadAccess?.can_download_full_book ? (
                <button
                  type="button"
                  onClick={handleDownloadPackage}
                  disabled={downloadLoading}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
                >
                  {downloadLoading
                    ? "Preparing download..."
                    : downloadAccess.package_available
                      ? "Download offline package"
                      : "Prepare offline package"}
                </button>
              ) : (
                <p className="text-sm text-slate-600">
                  {offlineDownloadsEnabled
                    ? (downloadAccess?.reason || "Premium subscription required for offline downloads.")
                    : "Offline downloads are not enabled for this release yet."}
                </p>
              )}
              {downloadError ? <p className="text-sm text-rose-600">{downloadError}</p> : null}
            </section>
          ) : null}
        </div>
      </details>

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
              className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
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
                className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white"
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

      {(isLastPage || completed) && canReadFullBook && (
        <StoryFeedbackForm
          bookId={book.book_id}
          token={isAuthenticated ? token : null}
          canSubmit={isAuthenticated}
          childProfileId={selectedChildProfile?.id ?? null}
          completed={true}
        />
      )}

      {(isLastPage || completed) && moreLikeThis.length ? (
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

      {(isLastPage || completed) && activeBedtimePackContext?.nextItem ? (
        <section className="space-y-3 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
          <h3 className="text-xl font-semibold text-slate-900">Next in tonight's pack</h3>
          <p className="text-sm text-slate-600">
            Keep the bedtime rhythm going with story {activeBedtimePackContext.nextItem.position}.
          </p>
          <Link
            href={`/reader/${activeBedtimePackContext.nextItem.book_id}`}
            className="inline-flex rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
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
