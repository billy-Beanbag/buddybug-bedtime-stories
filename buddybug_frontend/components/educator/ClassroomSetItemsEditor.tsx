"use client";

import { useMemo, useState } from "react";

import { apiDelete, apiGet, apiPost } from "@/lib/api";
import type {
  ClassroomSetDetailResponse,
  ClassroomSetRead,
  DiscoverySearchResponse,
  DiscoverySearchResult,
} from "@/lib/types";

function SearchResultCard({
  item,
  disabled,
  onAdd,
}: {
  item: DiscoverySearchResult;
  disabled: boolean;
  onAdd: (bookId: number) => Promise<void>;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-medium text-slate-900">{item.title}</h3>
          <p className="mt-1 text-xs text-slate-500">
            {item.age_band} • {item.language.toUpperCase()}
          </p>
        </div>
        <button
          type="button"
          disabled={disabled}
          onClick={() => void onAdd(item.book_id)}
          className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-900 disabled:opacity-60"
        >
          Add
        </button>
      </div>
    </div>
  );
}

export function ClassroomSetItemsEditor({
  classroomSet,
  detail,
  token,
  onChanged,
}: {
  classroomSet: ClassroomSetRead;
  detail: ClassroomSetDetailResponse;
  token: string;
  onChanged: () => Promise<void>;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<DiscoverySearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState<number | null>(null);
  const [removing, setRemoving] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const itemIdByBookId = useMemo(
    () => new Map(detail.set_items.map((item) => [item.book_id, item.id])),
    [detail.set_items],
  );

  async function handleSearch() {
    setSearching(true);
    setStatusMessage(null);
    try {
      const response = await apiGet<DiscoverySearchResponse>("/discovery/search", {
        token,
        query: {
          q: query || undefined,
          age_band: classroomSet.age_band || undefined,
          language: classroomSet.language || undefined,
          limit: 12,
        },
      });
      setResults(response.items);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Unable to search books");
    } finally {
      setSearching(false);
    }
  }

  async function handleAdd(bookId: number) {
    setSaving(bookId);
    setStatusMessage(null);
    try {
      await apiPost(
        `/educator/classroom-sets/${classroomSet.id}/items`,
        { book_id: bookId, position: detail.set_items.length + 1 },
        { token },
      );
      await onChanged();
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Unable to add book");
    } finally {
      setSaving(null);
    }
  }

  async function handleRemove(itemId: number) {
    setRemoving(itemId);
    setStatusMessage(null);
    try {
      await apiDelete(`/educator/classroom-set-items/${itemId}`, { token });
      await onChanged();
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Unable to remove book");
    } finally {
      setRemoving(null);
    }
  }

  return (
    <section className="space-y-5 rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Books in this classroom set</h2>
        <p className="mt-1 text-sm text-slate-600">
          Search Buddybug’s published catalog and add books that fit your classroom reading goal.
        </p>
      </div>

      <form
        className="flex flex-col gap-3 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSearch();
        }}
      >
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by title or keyword"
          className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
        />
        <button
          type="submit"
          disabled={searching}
          className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
        >
          {searching ? "Searching..." : "Search books"}
        </button>
      </form>

      {statusMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{statusMessage}</div>
      ) : null}

      <div className="grid gap-3">
        {detail.items.length ? (
          detail.items.map((item, index) => {
            const itemId = itemIdByBookId.get(item.book_id);
            return (
              <div key={`set-item-${item.book_id}`} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Position {index + 1}</p>
                    <h3 className="mt-1 font-medium text-slate-900">{item.title}</h3>
                    <p className="mt-1 text-xs text-slate-500">
                      {item.age_band} • {item.language.toUpperCase()}
                    </p>
                  </div>
                  {itemId ? (
                    <button
                      type="button"
                      disabled={removing === itemId}
                      onClick={() => void handleRemove(itemId)}
                      className="rounded-xl border border-rose-200 bg-white px-3 py-2 text-xs font-medium text-rose-700 disabled:opacity-60"
                    >
                      {removing === itemId ? "Removing..." : "Remove"}
                    </button>
                  ) : null}
                </div>
              </div>
            );
          })
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-4 text-sm text-slate-600">
            No books in this set yet. Search and add a few teacher-friendly reading options.
          </div>
        )}
      </div>

      {results.length ? (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Search results</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {results.map((item) => (
              <SearchResultCard
                key={`search-${item.book_id}`}
                item={item}
                disabled={itemIdByBookId.has(item.book_id) || saving === item.book_id}
                onAdd={handleAdd}
              />
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
