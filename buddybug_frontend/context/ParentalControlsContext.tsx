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
import { apiGet, apiPatch } from "@/lib/api";
import type { ParentalControlSettingsRead, ResolvedParentalControlsResponse } from "@/lib/types";

interface ParentalControlsContextValue {
  parentSettings: ParentalControlSettingsRead | null;
  resolvedControls: ResolvedParentalControlsResponse | null;
  isLoading: boolean;
  refreshParentalControls: () => Promise<void>;
  updateParentSettings: (payload: Partial<ParentalControlSettingsRead>) => Promise<ParentalControlSettingsRead>;
}

const ParentalControlsContext = createContext<ParentalControlsContextValue | undefined>(undefined);

export function ParentalControlsProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, token } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const [parentSettings, setParentSettings] = useState<ParentalControlSettingsRead | null>(null);
  const [resolvedControls, setResolvedControls] = useState<ResolvedParentalControlsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshParentalControls = useCallback(async () => {
    if (!isAuthenticated || !token) {
      setParentSettings(null);
      setResolvedControls(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const [settings, resolved] = await Promise.all([
        apiGet<ParentalControlSettingsRead>("/parental-controls/me", { token }),
        apiGet<ResolvedParentalControlsResponse>("/parental-controls/resolved", {
          token,
          query: { child_profile_id: selectedChildProfile?.id },
        }),
      ]);
      setParentSettings(settings);
      setResolvedControls(resolved);
    } catch {
      setParentSettings(null);
      setResolvedControls(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, selectedChildProfile?.id, token]);

  useEffect(() => {
    void refreshParentalControls();
  }, [refreshParentalControls]);

  const updateParentSettings = useCallback(
    async (payload: Partial<ParentalControlSettingsRead>) => {
      if (!token) {
        throw new Error("Authentication required");
      }
      const updated = await apiPatch<ParentalControlSettingsRead>("/parental-controls/me", payload, { token });
      setParentSettings(updated);
      const resolved = await apiGet<ResolvedParentalControlsResponse>("/parental-controls/resolved", {
        token,
        query: { child_profile_id: selectedChildProfile?.id },
      });
      setResolvedControls(resolved);
      return updated;
    },
    [selectedChildProfile?.id, token],
  );

  const value = useMemo<ParentalControlsContextValue>(
    () => ({
      parentSettings,
      resolvedControls,
      isLoading,
      refreshParentalControls,
      updateParentSettings,
    }),
    [isLoading, parentSettings, refreshParentalControls, resolvedControls, updateParentSettings],
  );

  return <ParentalControlsContext.Provider value={value}>{children}</ParentalControlsContext.Provider>;
}

export function useParentalControls() {
  const context = useContext(ParentalControlsContext);
  if (!context) {
    throw new Error("useParentalControls must be used within ParentalControlsProvider");
  }
  return context;
}
