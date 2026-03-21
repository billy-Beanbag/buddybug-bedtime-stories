"use client";

import { useEffect, useState } from "react";

import { useConnectivity } from "@/context/ConnectivityContext";
import { removeLibraryItem, saveBook, updateLibraryItem } from "@/lib/library";
import { queueSyncAction } from "@/lib/offline-sync";
import { removeOfflineBookPackage } from "@/lib/offline-storage";
import type { UserLibraryItemRead } from "@/lib/types";

interface SaveBookButtonProps {
  bookId: number;
  token: string | null;
  childProfileId?: number | null;
  language?: string;
  initialItem?: UserLibraryItemRead | null;
  canSaveOffline?: boolean;
  onChanged?: (item: UserLibraryItemRead | null) => void;
}

export function SaveBookButton({
  bookId,
  token,
  childProfileId,
  language,
  initialItem = null,
  canSaveOffline = false,
  onChanged,
}: SaveBookButtonProps) {
  const { isOnline } = useConnectivity();
  const [item, setItem] = useState<UserLibraryItemRead | null>(initialItem);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setItem(initialItem);
  }, [initialItem]);

  function applyNextItem(nextItem: UserLibraryItemRead | null) {
    setItem(nextItem);
    onChanged?.(nextItem);
  }

  async function handleSaveToggle() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      if (item && item.status !== "removed") {
        await removeLibraryItem(bookId, { token, childProfileId });
        applyNextItem(null);
      } else {
        const saved = await saveBook(bookId, { token, childProfileId, savedForOffline: item?.saved_for_offline ?? false });
        applyNextItem(saved);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update saved state");
    } finally {
      setLoading(false);
    }
  }

  async function handleOfflineToggle() {
    if (!token || !item) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const nextSavedForOffline = !item.saved_for_offline;
      if (!isOnline) {
        const optimisticItem = {
          ...item,
          saved_for_offline: nextSavedForOffline,
          updated_at: new Date().toISOString(),
        };
        applyNextItem(optimisticItem);
        if (!nextSavedForOffline && language) {
          await removeOfflineBookPackage(bookId, language).catch(() => undefined);
        }
        await queueSyncAction("library_offline_state", {
          book_id: bookId,
          child_profile_id: childProfileId ?? null,
          saved_for_offline: nextSavedForOffline,
        });
        return;
      }
      const updated = await updateLibraryItem(
        bookId,
        { saved_for_offline: nextSavedForOffline },
        { token, childProfileId },
      );
      if (!nextSavedForOffline && language) {
        await removeOfflineBookPackage(bookId, language).catch(() => undefined);
      }
      applyNextItem(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update offline state");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return null;
  }

  const isSaved = Boolean(item && item.status !== "removed");

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleSaveToggle}
          disabled={loading}
          className={`rounded-2xl px-4 py-2 text-sm font-medium disabled:opacity-60 ${
            isSaved ? "border border-slate-200 bg-white text-slate-900" : "bg-slate-900 text-white"
          }`}
        >
          {loading ? "Saving..." : isSaved ? "Saved" : "Save"}
        </button>
        {isSaved && canSaveOffline ? (
          <button
            type="button"
            onClick={handleOfflineToggle}
            disabled={loading}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900 disabled:opacity-60"
          >
            {item?.saved_for_offline ? "Offline marked" : "Save for offline"}
          </button>
        ) : null}
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
    </div>
  );
}
