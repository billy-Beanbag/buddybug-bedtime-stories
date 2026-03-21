"use client";

import type { OrganizationRead } from "@/lib/types";

export function OrganizationCard({ organization }: { organization: OrganizationRead }) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{organization.name}</h2>
          <p className="mt-1 text-sm text-slate-600">Slug: {organization.slug}</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            organization.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
          }`}
        >
          {organization.is_active ? "Active" : "Inactive"}
        </span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Created {new Date(organization.created_at).toLocaleString()}
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Updated {new Date(organization.updated_at).toLocaleString()}
        </div>
      </div>
    </section>
  );
}
