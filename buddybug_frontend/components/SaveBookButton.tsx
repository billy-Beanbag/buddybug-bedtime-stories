"use client";

import { useEffect, useState } from "react";

import { removeLibraryItem, saveBook } from "@/lib/library";
import type { UserLibraryItemRead } from "@/lib/types";

interface SaveBookButtonProps {
  bookId: number;
  token: string | null;
  childProfileId?: number | null;
  initialItem?: UserLibraryItemRead | null;
  onChanged?: (item: UserLibraryItemRead | null) => void;
}

export function SaveBookButton({
  bookId,
  token,
  childProfileId,
  initialItem = null,
  onChanged,
}: SaveBookButtonProps) {
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
        const saved = await saveBook(bookId, { token, childProfileId, savedForOffline: false });
        applyNextItem(saved);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update saved state");
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
      <div className="flex flex-wrap items-center gap-2">
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
        <p className="text-sm text-slate-600">
          {isSaved ? "Saved in your Buddybug library." : "Save this story to your Buddybug library."}
        </p>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
    </div>
  );
}
