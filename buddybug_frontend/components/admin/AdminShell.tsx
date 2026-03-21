"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useAuth } from "@/context/AuthContext";
import { AdminNav } from "@/components/admin/AdminNav";

export function AdminShell({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.96),_rgba(238,242,255,0.9)_42%,_rgba(226,232,240,0.92))]">
      <div className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-6 rounded-3xl border border-white/80 bg-white/90 px-5 py-4 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Buddybug Admin</p>
              <h1 className="mt-1 text-2xl font-semibold text-slate-900">{title}</h1>
              {description ? <p className="mt-2 text-sm text-slate-600">{description}</p> : null}
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-slate-700">
                {user?.display_name || user?.email || "Admin"}
              </span>
              <Link
                href="/library"
                className="rounded-2xl border border-slate-200 bg-white px-4 py-2 font-medium text-slate-900 transition hover:border-indigo-200 hover:bg-indigo-50/50"
              >
                View reader app
              </Link>
            </div>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">
          <aside>
            <AdminNav />
          </aside>
          <main className="min-w-0">{children}</main>
        </div>
      </div>
    </div>
  );
}
