"use client";

import { useSearchParams } from "next/navigation";

import { AdminCommandPalette } from "@/components/admin/AdminCommandPalette";

export default function AdminSearchPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Internal search console</h1>
        <p className="mt-2 text-sm text-slate-600">
          Search across core operational entities and use safe quick actions to move faster through Buddybug admin work.
        </p>
      </section>
      <AdminCommandPalette embedded initialQuery={initialQuery} />
    </div>
  );
}
