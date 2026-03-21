"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { ReengagementCard } from "@/components/ReengagementCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import {
  trackReengagementDashboardOpened,
  trackReengagementSuggestionDismissed,
  trackReengagementSuggestionViewed,
} from "@/lib/analytics";
import { apiGet, apiPatch } from "@/lib/api";
import type { ReengagementDashboardResponse, ReengagementSuggestionRead } from "@/lib/types";

interface ReengagementListProps {
  surface: "home" | "library" | "profile";
  title?: string;
  compact?: boolean;
  limit?: number;
}

const STATE_LABELS: Record<string, string> = {
  active: "A few gentle nudges based on recent reading.",
  new_but_inactive: "A small push to help Buddybug click after signup.",
  partially_activated: "A quick path back into setup and first sessions.",
  dormant_7d: "A warm reminder after a quiet week.",
  dormant_30d: "A softer win-back surface for families who have gone quiet.",
  lapsed_premium: "A return path for families who lost premium access.",
  preview_only_user: "A helpful reminder when preview behavior suggests upgrade interest.",
  unfinished_story_user: "A reminder built around stories that are already in progress.",
  saved_but_unread_user: "A reminder built around stories the family already saved.",
};

export function ReengagementList({
  surface,
  title = "Pick up where you left off",
  compact = false,
  limit = 3,
}: ReengagementListProps) {
  const { isAuthenticated, token, user } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const { locale } = useLocale();
  const [dashboard, setDashboard] = useState<ReengagementDashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [dismissingId, setDismissingId] = useState<number | null>(null);
  const trackedIdsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setDashboard(null);
      return;
    }

    async function loadDashboard() {
      setLoading(true);
      try {
        const response = await apiGet<ReengagementDashboardResponse>("/reengagement/me", { token });
        setDashboard(response);
        void trackReengagementDashboardOpened({
          token,
          user,
          language: locale,
          childProfileId: selectedChildProfile?.id,
          source: `${surface}_surface`,
        });
      } catch {
        setDashboard(null);
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, [isAuthenticated, locale, selectedChildProfile?.id, surface, token, user]);

  const visibleSuggestions = useMemo(() => {
    const suggestions = dashboard?.suggestions || [];
    const filtered = selectedChildProfile
      ? suggestions.filter(
          (suggestion) =>
            suggestion.child_profile_id === null || suggestion.child_profile_id === selectedChildProfile.id,
        )
      : suggestions;
    return filtered.slice(0, limit);
  }, [dashboard?.suggestions, limit, selectedChildProfile]);

  useEffect(() => {
    for (const suggestion of visibleSuggestions) {
      if (trackedIdsRef.current.has(suggestion.id)) {
        continue;
      }
      trackedIdsRef.current.add(suggestion.id);
      void trackReengagementSuggestionViewed(suggestion.suggestion_type, {
        token,
        user,
        language: locale,
        childProfileId: suggestion.child_profile_id,
        source: `${surface}_surface`,
        suggestionId: suggestion.id,
        relatedBookId: suggestion.related_book_id,
      });
    }
  }, [locale, surface, token, user, visibleSuggestions]);

  async function handleDismiss(suggestionId: number) {
    if (!token) {
      return;
    }
    setDismissingId(suggestionId);
    try {
      const updated = await apiPatch<ReengagementSuggestionRead>(
        `/reengagement/me/suggestions/${suggestionId}`,
        { is_dismissed: true },
        { token },
      );
      setDashboard((current) =>
        current
          ? {
              ...current,
              suggestions: current.suggestions.filter((suggestion) => suggestion.id !== updated.id),
            }
          : current,
      );
      void trackReengagementSuggestionDismissed(updated.suggestion_type, {
        token,
        user,
        language: locale,
        childProfileId: updated.child_profile_id,
        source: `${surface}_surface`,
        suggestionId: updated.id,
        relatedBookId: updated.related_book_id,
      });
    } finally {
      setDismissingId(null);
    }
  }

  if (!isAuthenticated || loading || !visibleSuggestions.length) {
    return null;
  }

  return (
    <section className="space-y-3">
      <div>
        <h2 className={`font-semibold text-slate-900 ${compact ? "text-xl" : "text-2xl"}`}>{title}</h2>
        <p className="mt-1 text-sm text-slate-600">
          {STATE_LABELS[dashboard?.engagement_state?.state_key || "active"] ||
            "Helpful reminders based on your recent reading activity."}
        </p>
      </div>
      <div className="grid gap-3">
        {visibleSuggestions.map((suggestion) => (
          <ReengagementCard
            key={suggestion.id}
            suggestion={suggestion}
            compact={compact}
            dismissing={dismissingId === suggestion.id}
            onDismiss={handleDismiss}
          />
        ))}
      </div>
    </section>
  );
}
