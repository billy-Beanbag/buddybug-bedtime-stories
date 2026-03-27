import type { ReactNode } from "react";

export function PrelaunchShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.98),rgba(238,242,255,0.92)_38%,rgba(224,231,255,0.82))] text-slate-900">
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 md:py-10">{children}</main>
    </div>
  );
}
