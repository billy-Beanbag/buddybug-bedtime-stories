"use client";

import { ADMIN_SELECTED_SURFACE } from "@/lib/admin-styles";
import type { InternalSearchGroup, InternalSearchResult } from "@/lib/types";

export function InternalSearchResults({
  groups,
  selectedKey,
  onHighlight,
  onSelect,
  emptyTitle = "No matching internal results",
  emptyDescription = "Try a broader search across users, drafts, tickets, incidents, and operational tools.",
}: {
  groups: InternalSearchGroup[];
  selectedKey: string | null;
  onHighlight: (item: InternalSearchResult) => void;
  onSelect: (item: InternalSearchResult) => void;
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  if (!groups.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
        <p className="font-medium text-slate-900">{emptyTitle}</p>
        <p className="mt-1">{emptyDescription}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <section key={group.entity_type} className="rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-slate-900">{group.label}</h3>
          </div>
          <div className="divide-y divide-slate-100">
            {group.items.map((item) => {
              const itemKey = `${item.entity_type}:${item.entity_id}`;
              const isSelected = itemKey === selectedKey;

              return (
                <button
                  key={itemKey}
                  type="button"
                  onMouseEnter={() => onHighlight(item)}
                  onFocus={() => onHighlight(item)}
                  onClick={() => onSelect(item)}
                  className={`flex w-full items-start justify-between gap-3 px-4 py-4 text-left transition ${
                    isSelected ? ADMIN_SELECTED_SURFACE : "hover:bg-slate-50"
                  }`}
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{item.title}</span>
                      {item.badge ? (
                        <span
                          className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
                            isSelected ? "bg-indigo-100 text-indigo-900" : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {item.badge}
                        </span>
                      ) : null}
                    </div>
                    {item.subtitle ? <p className={`mt-1 text-sm ${isSelected ? "text-indigo-700" : "text-slate-600"}`}>{item.subtitle}</p> : null}
                    {item.description ? (
                      <p className={`mt-2 text-sm ${isSelected ? "text-indigo-700/80" : "text-slate-500"}`}>{item.description}</p>
                    ) : null}
                  </div>
                  <div className={`shrink-0 text-xs ${isSelected ? "text-indigo-700/80" : "text-slate-400"}`}>{item.entity_id}</div>
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
