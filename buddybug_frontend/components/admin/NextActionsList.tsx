"use client";

import Link from "next/link";

import { ADMIN_CARD_HOVER } from "@/lib/admin-styles";
import type { AdminNextActionItem } from "@/lib/types";

function actionHref(item: AdminNextActionItem) {
  if (item.entity_type === "story_draft") {
    return `/admin/drafts/${item.entity_id}`;
  }
  if (item.entity_type === "story_page") {
    return "/admin/story-pages";
  }
  if (item.entity_type === "illustration") {
    return "/admin/illustrations";
  }
  if (item.entity_type === "book") {
    return "/admin/books";
  }
  if (item.entity_type === "book_audio") {
    return "/admin/audio";
  }
  return "/admin";
}

export function NextActionsList({ items }: { items: AdminNextActionItem[] }) {
  if (!items.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        No urgent workflow actions right now.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <Link
          key={`${item.entity_type}-${item.entity_id}-${item.stage}`}
          href={actionHref(item)}
          className={`block rounded-3xl border border-slate-200 bg-white p-4 shadow-sm ${ADMIN_CARD_HOVER}`}
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-900">{item.title}</p>
              <p className="mt-1 text-sm text-slate-600">
                {item.suggested_action} • {item.status}
              </p>
            </div>
            <div className="shrink-0 text-xs uppercase tracking-wide text-slate-500">{item.stage}</div>
          </div>
        </Link>
      ))}
    </div>
  );
}
