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
import { flushSyncQueue, getSyncQueueLength } from "@/lib/offline-sync";

interface ConnectivityContextValue {
  isOnline: boolean;
  lastOnlineAt: string | null;
  pendingSyncCount: number;
  refreshPendingSyncCount: () => Promise<void>;
  flushPendingSync: () => Promise<number>;
}

const ConnectivityContext = createContext<ConnectivityContextValue | undefined>(undefined);

function getNavigatorOnline() {
  if (typeof window === "undefined") {
    return true;
  }
  return window.navigator.onLine;
}

export function ConnectivityProvider({ children }: { children: ReactNode }) {
  const { token, user } = useAuth();
  const [isOnline, setIsOnline] = useState(getNavigatorOnline);
  const [lastOnlineAt, setLastOnlineAt] = useState<string | null>(() =>
    getNavigatorOnline() ? new Date().toISOString() : null,
  );
  const [pendingSyncCount, setPendingSyncCount] = useState(0);

  const refreshPendingSyncCount = useCallback(async () => {
    try {
      setPendingSyncCount(await getSyncQueueLength());
    } catch {
      setPendingSyncCount(0);
    }
  }, []);

  const flushPendingSync = useCallback(async () => {
    const flushedCount = await flushSyncQueue({ token, user });
    await refreshPendingSyncCount();
    return flushedCount;
  }, [refreshPendingSyncCount, token, user]);

  useEffect(() => {
    void refreshPendingSyncCount();
  }, [refreshPendingSyncCount]);

  useEffect(() => {
    function handleOnline() {
      setIsOnline(true);
      setLastOnlineAt(new Date().toISOString());
      void flushPendingSync();
    }

    function handleOffline() {
      setIsOnline(false);
      void refreshPendingSyncCount();
    }

    function handleSyncQueueChanged() {
      void refreshPendingSyncCount();
    }

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("buddybug:sync-queue-changed", handleSyncQueueChanged as EventListener);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("buddybug:sync-queue-changed", handleSyncQueueChanged as EventListener);
    };
  }, [flushPendingSync, refreshPendingSyncCount]);

  useEffect(() => {
    if (isOnline) {
      void flushPendingSync();
    }
  }, [flushPendingSync, isOnline]);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) {
      return;
    }
    void navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  }, []);

  const value = useMemo<ConnectivityContextValue>(
    () => ({
      isOnline,
      lastOnlineAt,
      pendingSyncCount,
      refreshPendingSyncCount,
      flushPendingSync,
    }),
    [flushPendingSync, isOnline, lastOnlineAt, pendingSyncCount, refreshPendingSyncCount],
  );

  return <ConnectivityContext.Provider value={value}>{children}</ConnectivityContext.Provider>;
}

export function useConnectivity() {
  const context = useContext(ConnectivityContext);
  if (!context) {
    throw new Error("useConnectivity must be used within ConnectivityProvider");
  }
  return context;
}
