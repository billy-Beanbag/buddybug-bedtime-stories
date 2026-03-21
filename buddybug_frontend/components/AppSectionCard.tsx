"use client";

import type { ReactNode } from "react";

interface AppSectionCardProps {
  title?: string;
  description?: string;
  children: ReactNode;
}

export function AppSectionCard({ title, description, children }: AppSectionCardProps) {
  return (
    <section className="space-y-3 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      {title ? (
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
          {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
