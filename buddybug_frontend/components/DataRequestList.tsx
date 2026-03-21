"use client";

import type { DataRequestRead } from "@/lib/types";

interface DataRequestListProps {
  title?: string;
  items: DataRequestRead[];
}

export function DataRequestList({ title = "Data requests", items }: DataRequestListProps) {
  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-600">
          Export and deletion requests are tracked here so you can follow progress over time.
        </p>
      </div>

      {items.length ? (
        <div className="space-y-3">
          {items.map((item) => (
            <article key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="font-medium text-slate-900">{item.request_type.replaceAll("_", " ")}</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Requested {new Date(item.requested_at).toLocaleString()}
                    {item.child_profile_id ? ` • Child profile ${item.child_profile_id}` : ""}
                  </p>
                </div>
                <span className="rounded-full bg-white px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-700">
                  {item.status}
                </span>
              </div>
              {item.reason ? <p className="mt-3 text-sm text-slate-700">Reason: {item.reason}</p> : null}
              {item.notes ? <p className="mt-2 text-sm text-slate-600">Notes: {item.notes}</p> : null}
              {item.output_url ? (
                <a
                  href={item.output_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900"
                >
                  Download export
                </a>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-4 text-sm text-slate-600">
          No data requests yet.
        </div>
      )}
    </section>
  );
}
