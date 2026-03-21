"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { OnboardingStartResponse, OnboardingStateRead } from "@/lib/types";

interface AdvanceOnboardingInput {
  next_step?: string;
  preferred_age_band?: string;
  preferred_language?: string;
  child_profile_created?: boolean;
  bedtime_mode_reviewed?: boolean;
  first_story_opened?: boolean;
}

interface OnboardingContextValue {
  state: OnboardingStateRead | null;
  isLoading: boolean;
  shouldShowOnboarding: boolean;
  refreshOnboarding: () => Promise<void>;
  advanceOnboarding: (payload?: AdvanceOnboardingInput) => Promise<OnboardingStartResponse | null>;
  skipOnboarding: () => Promise<OnboardingStateRead | null>;
  completeOnboarding: () => Promise<OnboardingStateRead | null>;
}

const OnboardingContext = createContext<OnboardingContextValue | undefined>(undefined);

export function getOnboardingRoute(step: string | undefined | null) {
  switch (step) {
    case "welcome":
      return "/onboarding";
    case "child_setup":
      return "/onboarding/child";
    case "preferences":
      return "/onboarding/preferences";
    case "bedtime_mode":
      return "/onboarding/bedtime";
    case "first_story":
      return "/onboarding/first-story";
    default:
      return "/library";
  }
}

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const [state, setState] = useState<OnboardingStateRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshOnboarding = useCallback(async () => {
    if (!isAuthenticated || !token) {
      setState(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiGet<OnboardingStateRead>("/onboarding/me", { token });
      setState(response);
    } catch {
      setState(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (authLoading) {
      return;
    }
    void refreshOnboarding();
  }, [authLoading, refreshOnboarding]);

  const advanceOnboarding = useCallback(
    async (payload?: AdvanceOnboardingInput) => {
      if (!token || !isAuthenticated) {
        return null;
      }
      const response = await apiPost<OnboardingStartResponse>("/onboarding/me/advance", payload ?? {}, { token });
      setState(response.state);
      return response;
    },
    [isAuthenticated, token],
  );

  const skipOnboarding = useCallback(async () => {
    if (!token || !isAuthenticated) {
      return null;
    }
    const response = await apiPost<OnboardingStateRead>("/onboarding/me/skip", undefined, { token });
    setState(response);
    return response;
  }, [isAuthenticated, token]);

  const completeOnboarding = useCallback(async () => {
    if (!token || !isAuthenticated) {
      return null;
    }
    const response = await apiPost<OnboardingStateRead>("/onboarding/me/complete", undefined, { token });
    setState(response);
    return response;
  }, [isAuthenticated, token]);

  const value = useMemo<OnboardingContextValue>(
    () => ({
      state,
      isLoading,
      shouldShowOnboarding: Boolean(isAuthenticated && state && !state.completed && !state.skipped),
      refreshOnboarding,
      advanceOnboarding,
      skipOnboarding,
      completeOnboarding,
    }),
    [advanceOnboarding, completeOnboarding, isAuthenticated, isLoading, refreshOnboarding, skipOnboarding, state],
  );

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error("useOnboarding must be used within OnboardingProvider");
  }
  return context;
}
