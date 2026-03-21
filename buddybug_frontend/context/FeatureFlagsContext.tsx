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
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import { fetchFeatureFlagBundle } from "@/lib/feature-flags";

interface FeatureFlagsContextValue {
  flags: Record<string, boolean>;
  refreshFlags: () => Promise<void>;
  isEnabled: (key: string) => boolean;
}

const FeatureFlagsContext = createContext<FeatureFlagsContextValue | undefined>(undefined);

export function FeatureFlagsProvider({ children }: { children: ReactNode }) {
  const { isLoading: authLoading, token, user } = useAuth();
  const { isLoading: childProfilesLoading, selectedChildProfile } = useChildProfiles();
  const { locale } = useLocale();
  const [flags, setFlags] = useState<Record<string, boolean>>({});

  const refreshFlags = useCallback(async () => {
    try {
      const bundle = await fetchFeatureFlagBundle({
        token,
        user,
        childProfileId: selectedChildProfile?.id,
        language: selectedChildProfile?.language || locale,
      });
      setFlags(bundle.flags);
    } catch {
      setFlags({});
    }
  }, [locale, selectedChildProfile?.id, selectedChildProfile?.language, token, user]);

  useEffect(() => {
    if (authLoading || childProfilesLoading) {
      return;
    }
    void refreshFlags();
  }, [authLoading, childProfilesLoading, refreshFlags]);

  const value = useMemo<FeatureFlagsContextValue>(
    () => ({
      flags,
      refreshFlags,
      isEnabled: (key: string) => Boolean(flags[key]),
    }),
    [flags, refreshFlags],
  );

  return <FeatureFlagsContext.Provider value={value}>{children}</FeatureFlagsContext.Provider>;
}

export function useFeatureFlags() {
  const context = useContext(FeatureFlagsContext);
  if (!context) {
    throw new Error("useFeatureFlags must be used within FeatureFlagsProvider");
  }
  return context;
}
