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
import { apiGet } from "@/lib/api";
import type { ChildProfileRead } from "@/lib/types";

const STORAGE_KEY = "buddybug.selected-child-profile-id";

interface ChildProfileContextValue {
  childProfiles: ChildProfileRead[];
  selectedChildProfile: ChildProfileRead | null;
  isLoading: boolean;
  setSelectedChildProfile: (childProfileId: number | null) => void;
  refreshChildProfiles: () => Promise<void>;
}

const ChildProfileContext = createContext<ChildProfileContextValue | undefined>(undefined);

function readStoredSelectedId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = window.localStorage.getItem(STORAGE_KEY);
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function persistSelectedId(childProfileId: number | null) {
  if (typeof window === "undefined") {
    return;
  }
  if (childProfileId === null) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, String(childProfileId));
}

export function ChildProfileProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, token } = useAuth();
  const [childProfiles, setChildProfiles] = useState<ChildProfileRead[]>([]);
  const [selectedChildProfileId, setSelectedChildProfileId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshChildProfiles = useCallback(async () => {
    if (!isAuthenticated || !token) {
      setChildProfiles([]);
      setSelectedChildProfileId(null);
      setIsLoading(false);
      persistSelectedId(null);
      return;
    }

    setIsLoading(true);
    try {
      const profiles = await apiGet<ChildProfileRead[]>("/child-profiles", { token });
      const activeProfiles = profiles.filter((profile) => profile.is_active);
      setChildProfiles(activeProfiles);
      const storedId = readStoredSelectedId();
      const hasStored = activeProfiles.some((profile) => profile.id === storedId);
      const nextId = hasStored ? storedId : (activeProfiles[0]?.id ?? null);
      setSelectedChildProfileId(nextId);
      persistSelectedId(nextId);
    } catch {
      setChildProfiles([]);
      setSelectedChildProfileId(null);
      persistSelectedId(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (!isAuthenticated) {
      setChildProfiles([]);
      setSelectedChildProfileId(null);
      setIsLoading(false);
      persistSelectedId(null);
      return;
    }
    void refreshChildProfiles();
  }, [isAuthenticated, refreshChildProfiles]);

  const setSelectedChildProfile = useCallback(
    (childProfileId: number | null) => {
      const nextId =
        childProfileId !== null && childProfiles.some((profile) => profile.id === childProfileId)
          ? childProfileId
          : null;
      setSelectedChildProfileId(nextId);
      persistSelectedId(nextId);
    },
    [childProfiles],
  );

  const selectedChildProfile = useMemo(
    () => childProfiles.find((profile) => profile.id === selectedChildProfileId) ?? null,
    [childProfiles, selectedChildProfileId],
  );

  const value = useMemo<ChildProfileContextValue>(
    () => ({
      childProfiles,
      selectedChildProfile,
      isLoading,
      setSelectedChildProfile,
      refreshChildProfiles,
    }),
    [childProfiles, isLoading, refreshChildProfiles, selectedChildProfile, setSelectedChildProfile],
  );

  return <ChildProfileContext.Provider value={value}>{children}</ChildProfileContext.Provider>;
}

export function useChildProfiles() {
  const context = useContext(ChildProfileContext);
  if (!context) {
    throw new Error("useChildProfiles must be used within ChildProfileProvider");
  }
  return context;
}
