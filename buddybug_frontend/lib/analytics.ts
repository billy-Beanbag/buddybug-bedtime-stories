"use client";

import { getReaderIdentifier } from "@/lib/auth";
import { resolveApiUrl } from "@/lib/api";
import type { AnalyticsTrackRequest, User } from "@/lib/types";

const ANALYTICS_SESSION_KEY = "buddybug.analytics.session";

function canUseBrowserStorage() {
  return typeof window !== "undefined";
}

function createAnalyticsSessionId() {
  const random = Math.random().toString(36).slice(2, 10);
  return `session:${random}`;
}

export function getAnalyticsSessionId() {
  if (!canUseBrowserStorage()) {
    return "session:server";
  }
  const stored = window.sessionStorage.getItem(ANALYTICS_SESSION_KEY);
  if (stored) {
    return stored;
  }
  const sessionId = createAnalyticsSessionId();
  window.sessionStorage.setItem(ANALYTICS_SESSION_KEY, sessionId);
  return sessionId;
}

interface TrackOptions {
  token?: string | null;
  user?: User | null;
  readerIdentifier?: string;
  childProfileId?: number | null;
}

export async function trackEvent(event: AnalyticsTrackRequest, options?: TrackOptions) {
  try {
    const readerIdentifier = options?.readerIdentifier || getReaderIdentifier(options?.user);
    await fetch(resolveApiUrl("/analytics/track"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Reader-Identifier": readerIdentifier,
        ...(options?.token ? { Authorization: `Bearer ${options.token}` } : {}),
      },
      body: JSON.stringify({
        ...event,
        child_profile_id: options?.childProfileId ?? event.child_profile_id,
        session_id: event.session_id || getAnalyticsSessionId(),
      }),
      keepalive: true,
    });
  } catch {
    // Analytics should never block the user experience.
  }
}

export function trackAppOpened(options?: TrackOptions & { language?: string }) {
  return trackEvent(
    {
      event_name: "app_opened",
      language: options?.language,
      metadata: { source: "frontend_home" },
    },
    options,
  );
}

export function trackLibraryViewed(options?: TrackOptions & { language?: string }) {
  return trackEvent(
    {
      event_name: "library_viewed",
      language: options?.language,
      metadata: { source: "frontend_library" },
    },
    options,
  );
}

export function trackBookOpened(bookId: number, options?: TrackOptions & { language?: string; source?: string }) {
  return trackEvent(
    {
      event_name: "book_opened",
      book_id: bookId,
      language: options?.language,
      metadata: { source: options?.source || "frontend_reader" },
    },
    options,
  );
}

export function trackPageViewed(
  bookId: number,
  pageNumber: number,
  options?: TrackOptions & { language?: string },
) {
  return trackEvent(
    {
      event_name: "book_page_viewed",
      book_id: bookId,
      language: options?.language,
      metadata: { page_number: pageNumber, source: "frontend_reader" },
    },
    options,
  );
}

export function trackBookCompleted(bookId: number, options?: TrackOptions & { language?: string; source?: string }) {
  return trackEvent(
    {
      event_name: "book_completed",
      book_id: bookId,
      language: options?.language,
      metadata: { source: options?.source || "frontend_reader_completion" },
    },
    options,
  );
}

export function trackAudioStarted(
  bookId: number,
  voiceDisplayName: string,
  options?: TrackOptions & { language?: string },
) {
  return trackEvent(
    {
      event_name: "audio_started",
      book_id: bookId,
      language: options?.language,
      metadata: { voice_display_name: voiceDisplayName, source: "frontend_audio_player" },
    },
    options,
  );
}

export function trackAudioCompleted(
  bookId: number,
  voiceDisplayName: string,
  options?: TrackOptions & { language?: string },
) {
  return trackEvent(
    {
      event_name: "audio_completed",
      book_id: bookId,
      language: options?.language,
      metadata: { voice_display_name: voiceDisplayName, source: "frontend_audio_player" },
    },
    options,
  );
}

export function trackVoiceSelected(
  bookId: number,
  voiceKey: string,
  options?: TrackOptions & { language?: string },
) {
  return trackEvent(
    {
      event_name: "voice_selected",
      book_id: bookId,
      language: options?.language,
      metadata: { voice_key: voiceKey, source: "frontend_voice_selector" },
    },
    options,
  );
}

export function trackBedtimeModeUsed(bookId: number | undefined, options?: TrackOptions & { language?: string; source?: string }) {
  return trackEvent(
    {
      event_name: "bedtime_mode_used",
      book_id: bookId,
      language: options?.language,
      metadata: { source: options?.source || "frontend_bedtime_mode" },
    },
    options,
  );
}

export function trackAutoplayBlockedByParentalControls(
  bookId: number,
  options?: TrackOptions & { language?: string },
) {
  return trackEvent(
    {
      event_name: "autoplay_blocked_by_parental_controls",
      book_id: bookId,
      language: options?.language,
      metadata: { source: "frontend_story_audio_player" },
    },
    options,
  );
}

export function trackAgeBandFilteredByParentalControls(options?: TrackOptions & { language?: string; source?: string }) {
  return trackEvent(
    {
      event_name: "age_band_filtered_by_parental_controls",
      language: options?.language,
      metadata: { source: options?.source || "frontend_parental_controls" },
    },
    options,
  );
}

export function trackRecommendationViewed(
  bookIds: number[],
  options?: TrackOptions & { language?: string; source?: string },
) {
  return trackEvent(
    {
      event_name: "recommendation_viewed",
      language: options?.language,
      metadata: { book_ids: bookIds, source: options?.source || "frontend_recommendations" },
    },
    options,
  );
}

export function trackRecommendationClicked(
  bookId: number,
  options?: TrackOptions & { language?: string; source?: string },
) {
  return trackEvent(
    {
      event_name: "recommendation_clicked",
      book_id: bookId,
      language: options?.language,
      metadata: { source: options?.source || "frontend_recommendations" },
    },
    options,
  );
}

export function trackPreviewWallHit(bookId: number, options?: TrackOptions & { language?: string }) {
  return trackEvent(
    {
      event_name: "preview_wall_hit",
      book_id: bookId,
      language: options?.language,
      metadata: { source: "frontend_preview_wall" },
    },
    options,
  );
}

export function trackLanguageChanged(
  nextLanguage: string,
  options?: TrackOptions & { previousLanguage?: string; source?: string },
) {
  return trackEvent(
    {
      event_name: "language_changed",
      language: nextLanguage,
      metadata: {
        previous_language: options?.previousLanguage || null,
        source: options?.source || "frontend_language_selector",
      },
    },
    options,
  );
}

export function trackDiscoverySearch(
  query: string | undefined,
  options?: TrackOptions & { language?: string; resultCount?: number; source?: string },
) {
  return trackEvent(
    {
      event_name: "discovery_search",
      language: options?.language,
      metadata: {
        q: query || null,
        result_count: options?.resultCount ?? null,
        source: options?.source || "frontend_discover",
      },
    },
    options,
  );
}

export function trackDiscoveryCollectionOpened(
  collectionKey: string,
  options?: TrackOptions & { language?: string; source?: string },
) {
  return trackEvent(
    {
      event_name: "discovery_collection_opened",
      language: options?.language,
      metadata: { collection_key: collectionKey, source: options?.source || "frontend_discover" },
    },
    options,
  );
}

export function trackDiscoveryBookOpened(
  bookId: number,
  options?: TrackOptions & { language?: string; source?: string },
) {
  return trackEvent(
    {
      event_name: "discovery_book_opened",
      book_id: bookId,
      language: options?.language,
      metadata: { source: options?.source || "frontend_discover" },
    },
    options,
  );
}

export function trackFeaturedCollectionViewed(
  options?: TrackOptions & { language?: string; count?: number; source?: string },
) {
  return trackEvent(
    {
      event_name: "featured_collection_viewed",
      language: options?.language,
      metadata: {
        count: options?.count ?? null,
        source: options?.source || "frontend_discover",
      },
    },
    options,
  );
}

export function trackMarketingPageViewed({
  eventName,
  source,
  token,
  user,
  language,
}: TrackOptions & {
  eventName:
    | "marketing_home_viewed"
    | "marketing_pricing_viewed"
    | "marketing_features_viewed"
    | "marketing_faq_viewed";
  source: string;
  language?: string;
}) {
  return trackEvent(
    {
      event_name: eventName,
      language,
      metadata: { source },
    },
    { token, user },
  );
}

export function trackMarketingCtaClicked({
  token,
  user,
  source,
  target,
  ctaLabel,
  language,
}: TrackOptions & {
  source: string;
  target: string;
  ctaLabel: string;
  language?: string;
}) {
  return trackEvent(
    {
      event_name: "marketing_cta_clicked",
      language,
      metadata: {
        source,
        target,
        cta_label: ctaLabel,
      },
    },
    { token, user },
  );
}

export function trackOfflineBookSaved(
  bookId: number,
  options?: TrackOptions & { language?: string; source?: string; packageVersion?: number },
) {
  return trackEvent(
    {
      event_name: "offline_book_saved",
      book_id: bookId,
      language: options?.language,
      metadata: {
        source: options?.source || "frontend_offline_download",
        package_version: options?.packageVersion ?? null,
      },
    },
    options,
  );
}

export function trackOfflineReaderOpened(
  bookId: number,
  options?: TrackOptions & { language?: string; source?: string },
) {
  return trackEvent(
    {
      event_name: "offline_reader_opened",
      book_id: bookId,
      language: options?.language,
      metadata: { source: options?.source || "frontend_offline_reader" },
    },
    options,
  );
}

export function trackSettingsOpened(options?: TrackOptions & { source?: string; language?: string }) {
  return trackEvent(
    {
      event_name: "settings_opened",
      language: options?.language,
      metadata: { source: options?.source || "settings_hub" },
    },
    options,
  );
}

export function trackDownloadsSettingsOpened(options?: TrackOptions & { source?: string; language?: string }) {
  return trackEvent(
    {
      event_name: "downloads_settings_opened",
      language: options?.language,
      metadata: { source: options?.source || "settings_downloads" },
    },
    options,
  );
}

export function trackAboutOpened(options?: TrackOptions & { source?: string; language?: string }) {
  return trackEvent(
    {
      event_name: "about_opened",
      language: options?.language,
      metadata: { source: options?.source || "settings_about" },
    },
    options,
  );
}

export function trackAppShellNavigationUsed(
  destination: string,
  options?: TrackOptions & { source?: string; language?: string },
) {
  return trackEvent(
    {
      event_name: "app_shell_navigation_used",
      language: options?.language,
      metadata: {
        destination,
        source: options?.source || "app_shell_navigation",
      },
    },
    options,
  );
}

export function trackOnboardingStarted(options?: TrackOptions & { source?: string; language?: string }) {
  return trackEvent(
    {
      event_name: "onboarding_started",
      language: options?.language,
      metadata: { source: options?.source || "onboarding_welcome" },
    },
    options,
  );
}

export function trackOnboardingStepCompleted(
  step: string,
  options?: TrackOptions & { source?: string; language?: string },
) {
  return trackEvent(
    {
      event_name: "onboarding_step_completed",
      language: options?.language,
      metadata: {
        step,
        source: options?.source || "onboarding_step",
      },
    },
    options,
  );
}

export function trackOnboardingSkipped(options?: TrackOptions & { source?: string; language?: string }) {
  return trackEvent(
    {
      event_name: "onboarding_skipped",
      language: options?.language,
      metadata: { source: options?.source || "onboarding_flow" },
    },
    options,
  );
}

export function trackOnboardingCompleted(options?: TrackOptions & { source?: string; language?: string }) {
  return trackEvent(
    {
      event_name: "onboarding_completed",
      language: options?.language,
      metadata: { source: options?.source || "onboarding_flow" },
    },
    options,
  );
}

export function trackOnboardingFirstStoryOpened(
  bookId: number,
  options?: TrackOptions & { source?: string; language?: string },
) {
  return trackEvent(
    {
      event_name: "onboarding_first_story_opened",
      book_id: bookId,
      language: options?.language,
      metadata: { source: options?.source || "onboarding_first_story" },
    },
    options,
  );
}

export function trackReengagementDashboardOpened(options?: TrackOptions & { source?: string; language?: string }) {
  return trackEvent(
    {
      event_name: "reengagement_dashboard_opened",
      language: options?.language,
      metadata: { source: options?.source || "reengagement_surface" },
    },
    options,
  );
}

export function trackReengagementSuggestionViewed(
  suggestionType: string,
  options?: TrackOptions & {
    source?: string;
    language?: string;
    suggestionId?: number;
    relatedBookId?: number | null;
  },
) {
  return trackEvent(
    {
      event_name: "reengagement_suggestion_viewed",
      book_id: options?.relatedBookId ?? undefined,
      language: options?.language,
      metadata: {
        suggestion_id: options?.suggestionId ?? null,
        suggestion_type: suggestionType,
        source: options?.source || "reengagement_surface",
      },
    },
    options,
  );
}

export function trackReengagementSuggestionDismissed(
  suggestionType: string,
  options?: TrackOptions & {
    source?: string;
    language?: string;
    suggestionId?: number;
    relatedBookId?: number | null;
  },
) {
  return trackEvent(
    {
      event_name: "reengagement_suggestion_dismissed",
      book_id: options?.relatedBookId ?? undefined,
      language: options?.language,
      metadata: {
        suggestion_id: options?.suggestionId ?? null,
        suggestion_type: suggestionType,
        source: options?.source || "reengagement_surface",
      },
    },
    options,
  );
}

export function trackMessageVariantExposed(
  surface: string,
  options?: TrackOptions & {
    language?: string;
    experimentKey?: string;
    experimentVariant?: string;
    source?: string;
  },
) {
  return trackEvent(
    {
      event_name: "message_variant_exposed",
      language: options?.language,
      experiment_key: options?.experimentKey,
      experiment_variant: options?.experimentVariant,
      metadata: {
        surface,
        source: options?.source || surface,
      },
    },
    options,
  );
}

export function trackMessageVariantClicked(
  surface: string,
  options?: TrackOptions & {
    language?: string;
    experimentKey?: string;
    experimentVariant?: string;
    source?: string;
    target?: string;
  },
) {
  return trackEvent(
    {
      event_name: "message_variant_clicked",
      language: options?.language,
      experiment_key: options?.experimentKey,
      experiment_variant: options?.experimentVariant,
      metadata: {
        surface,
        source: options?.source || surface,
        target: options?.target || null,
      },
    },
    options,
  );
}

export function trackPreviewWallUpgradeClicked(
  options?: TrackOptions & {
    language?: string;
    experimentKey?: string;
    experimentVariant?: string;
    source?: string;
  },
) {
  return trackEvent(
    {
      event_name: "preview_wall_upgrade_clicked",
      language: options?.language,
      experiment_key: options?.experimentKey,
      experiment_variant: options?.experimentVariant,
      metadata: {
        source: options?.source || "preview_wall",
      },
    },
    options,
  );
}

export function trackPricingCtaClicked(
  options?: TrackOptions & {
    language?: string;
    experimentKey?: string;
    experimentVariant?: string;
    source?: string;
    target?: string;
  },
) {
  return trackEvent(
    {
      event_name: "pricing_cta_clicked",
      language: options?.language,
      experiment_key: options?.experimentKey,
      experiment_variant: options?.experimentVariant,
      metadata: {
        source: options?.source || "pricing_cta",
        target: options?.target || null,
      },
    },
    options,
  );
}
