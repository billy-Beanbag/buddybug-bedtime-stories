"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type {
  InternalSearchResponse,
  InternalSearchResult,
  QuickActionItem,
  QuickActionResponse,
} from "@/lib/types";
import { InternalSearchResults } from "@/components/admin/InternalSearchResults";

const EMPTY_RESULTS: InternalSearchResponse = {
  query: "",
  groups: [],
};

function itemKey(item: InternalSearchResult) {
  return `${item.entity_type}:${item.entity_id}`;
}

export function AdminCommandPalette({
  open = false,
  onClose,
  embedded = false,
  initialQuery = "",
}: {
  open?: boolean;
  onClose?: () => void;
  embedded?: boolean;
  initialQuery?: string;
}) {
  const router = useRouter();
  const { token } = useAuth();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const isActive = embedded || open;
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<InternalSearchResponse>(EMPTY_RESULTS);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [actions, setActions] = useState<QuickActionItem[]>([]);
  const [actionsLoading, setActionsLoading] = useState(false);
  const [actionsError, setActionsError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  useEffect(() => {
    if (!isActive) {
      return;
    }
    const timeout = window.setTimeout(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    }, 20);
    return () => window.clearTimeout(timeout);
  }, [isActive]);

  useEffect(() => {
    if (!isActive || !token) {
      return;
    }

    const trimmedQuery = query.trim();
    if (trimmedQuery.length < 2) {
      setResults({ query: trimmedQuery, groups: [] });
      setLoading(false);
      setErrorMessage(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setErrorMessage(null);
    const timeout = window.setTimeout(() => {
      void apiGet<InternalSearchResponse>("/admin/search", {
        token,
        query: { q: trimmedQuery, limit_per_group: embedded ? 8 : 5 },
      })
        .then((response) => {
          if (!cancelled) {
            setResults(response);
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setErrorMessage(err instanceof Error ? err.message : "Unable to search internal entities");
            setResults({ query: trimmedQuery, groups: [] });
          }
        })
        .finally(() => {
          if (!cancelled) {
            setLoading(false);
          }
        });
    }, 160);

    return () => {
      cancelled = true;
      window.clearTimeout(timeout);
    };
  }, [embedded, isActive, query, token]);

  const flattenedResults = useMemo(
    () => results.groups.flatMap((group) => group.items),
    [results.groups],
  );
  const selectedItem = selectedIndex >= 0 ? flattenedResults[selectedIndex] ?? null : null;
  const selectedKey = selectedItem ? itemKey(selectedItem) : null;

  useEffect(() => {
    if (!flattenedResults.length) {
      setSelectedIndex(-1);
      return;
    }
    setSelectedIndex((current) => {
      if (current >= 0 && current < flattenedResults.length) {
        return current;
      }
      return 0;
    });
  }, [flattenedResults]);

  useEffect(() => {
    if (!isActive || !token) {
      return;
    }

    let cancelled = false;
    setActionsLoading(true);
    setActionsError(null);

    void apiGet<QuickActionResponse>("/admin/search/actions", {
      token,
      query: selectedItem
        ? {
            entity_type: selectedItem.entity_type,
            entity_id: selectedItem.entity_id,
          }
        : {
            q: query.trim() || undefined,
          },
    })
      .then((response) => {
        if (!cancelled) {
          setActions(response.items);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setActions([]);
          setActionsError(err instanceof Error ? err.message : "Unable to load quick actions");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setActionsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [isActive, query, selectedItem, token]);

  function closePalette() {
    if (!embedded) {
      onClose?.();
    }
  }

  function navigateTo(route: string) {
    router.push(route);
    closePalette();
  }

  async function runQuickAction(action: QuickActionItem) {
    setStatusMessage(null);
    if (action.action_type === "copy") {
      const valueToCopy = action.entity_id || "";
      if (!valueToCopy) {
        return;
      }
      try {
        await navigator.clipboard.writeText(valueToCopy);
        setStatusMessage(`Copied ${valueToCopy}.`);
      } catch {
        setStatusMessage("Unable to copy to clipboard.");
      }
      return;
    }

    if (action.route) {
      navigateTo(action.route);
    }
  }

  function handleSelectResult(item: InternalSearchResult) {
    if (item.route) {
      navigateTo(item.route);
      return;
    }
    const nextIndex = flattenedResults.findIndex((candidate) => itemKey(candidate) === itemKey(item));
    setSelectedIndex(nextIndex);
  }

  function handleHighlight(item: InternalSearchResult) {
    const nextIndex = flattenedResults.findIndex((candidate) => itemKey(candidate) === itemKey(item));
    if (nextIndex >= 0) {
      setSelectedIndex(nextIndex);
    }
  }

  if (!isActive) {
    return null;
  }

  const content = (
    <div className={`space-y-4 ${embedded ? "" : "rounded-[28px] border border-slate-200 bg-white p-5 shadow-2xl"}`}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{embedded ? "Internal search console" : "Command palette"}</h2>
          <p className="mt-1 text-sm text-slate-600">
            Search users, drafts, tickets, incidents, flags, and other internal entities from one place.
          </p>
        </div>
        {!embedded ? (
          <button
            type="button"
            onClick={closePalette}
            className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"
          >
            Close
          </button>
        ) : null}
      </div>

      <div className="flex items-center gap-3">
        <input
          ref={inputRef}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Escape" && !embedded) {
              event.preventDefault();
              closePalette();
              return;
            }
            if (event.key === "ArrowDown" && flattenedResults.length) {
              event.preventDefault();
              setSelectedIndex((current) => (current + 1) % flattenedResults.length);
              return;
            }
            if (event.key === "ArrowUp" && flattenedResults.length) {
              event.preventDefault();
              setSelectedIndex((current) => (current <= 0 ? flattenedResults.length - 1 : current - 1));
              return;
            }
            if (event.key === "Enter" && selectedItem?.route) {
              event.preventDefault();
              navigateTo(selectedItem.route);
            }
          }}
          placeholder="Search users, drafts, tickets, incidents, flags..."
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-0"
        />
        {!embedded ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500">
            Ctrl/Cmd+K
          </div>
        ) : null}
      </div>

      {statusMessage ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      {loading ? <div className="text-sm text-slate-500">Searching internal entities...</div> : null}

      <InternalSearchResults
        groups={results.groups}
        selectedKey={selectedKey}
        onHighlight={handleHighlight}
        onSelect={handleSelectResult}
        emptyTitle={query.trim().length < 2 ? "Type at least 2 characters" : "No matching internal results"}
        emptyDescription={
          query.trim().length < 2
            ? "Start typing to search users, books, drafts, incidents, campaigns, and operations tooling."
            : "Try a broader term or use the quick actions below."
        }
      />

      <section className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Quick actions</h3>
            <p className="mt-1 text-sm text-slate-600">
              {selectedItem
                ? `Safe actions for ${selectedItem.title}`
                : "Safe internal navigation shortcuts filtered by your current query."}
            </p>
          </div>
          {actionsLoading ? <span className="text-xs text-slate-500">Loading...</span> : null}
        </div>
        {actionsError ? <p className="mt-3 text-sm text-rose-600">{actionsError}</p> : null}
        {actions.length ? (
          <div className="mt-4 flex flex-wrap gap-3">
            {actions.map((action) => (
              <button
                key={action.key}
                type="button"
                onClick={() => void runQuickAction(action)}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm shadow-sm"
              >
                <div className="font-medium text-slate-900">{action.label}</div>
                {action.description ? <div className="mt-1 text-slate-600">{action.description}</div> : null}
              </button>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No quick actions available yet for this context.</p>
        )}
      </section>
    </div>
  );

  if (embedded) {
    return content;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/40 px-4 py-10" onClick={closePalette}>
      <div className="w-full max-w-4xl" onClick={(event) => event.stopPropagation()}>
        {content}
      </div>
    </div>
  );
}
