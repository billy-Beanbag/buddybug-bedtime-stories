"use client";

import Link from "next/link";

export interface AppSettingsListItem {
  href: string;
  title: string;
  description?: string;
  badge?: string | null;
}

interface AppSettingsListProps {
  items: AppSettingsListItem[];
}

export function AppSettingsList({ items }: AppSettingsListProps) {
  return (
    <div className="divide-y divide-slate-100 overflow-hidden rounded-3xl border border-slate-200 bg-white">
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="flex items-start justify-between gap-3 px-4 py-4 transition hover:bg-slate-50"
        >
          <div className="min-w-0">
            <p className="font-medium text-slate-900">{item.title}</p>
            {item.description ? <p className="mt-1 text-sm text-slate-600">{item.description}</p> : null}
          </div>
          <div className="shrink-0 text-right">
            {item.badge ? (
              <span className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700">
                {item.badge}
              </span>
            ) : null}
            <div className="mt-1 text-sm text-slate-400">Open</div>
          </div>
        </Link>
      ))}
    </div>
  );
}
