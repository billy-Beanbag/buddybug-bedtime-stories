"use client";

import type { NotificationEventRead } from "@/lib/types";

export function NotificationList({
  items,
  onToggleRead,
}: {
  items: NotificationEventRead[];
  onToggleRead: (item: NotificationEventRead) => Promise<void> | void;
}) {
  if (!items.length) {
    return (
      <div className="rounded-[2rem] border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        No notifications yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <article
          key={item.id}
          className={`rounded-[2rem] border p-4 shadow-sm ${
            item.is_read ? "border-slate-200 bg-white/80" : "border-indigo-200 bg-indigo-50/80"
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-1 text-sm text-slate-700">{item.body}</p>
              <p className="mt-2 text-xs text-slate-500">
                {item.notification_type.replaceAll("_", " ")} • {new Date(item.created_at).toLocaleString()}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void onToggleRead(item)}
              className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-800"
            >
              {item.is_read ? "Mark unread" : "Mark read"}
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}
