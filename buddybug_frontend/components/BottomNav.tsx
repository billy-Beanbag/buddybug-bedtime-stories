"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { trackAppShellNavigationUsed } from "@/lib/analytics";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/library", label: "Library" },
  { href: "/continue-reading", label: "Continue" },
  { href: "/settings", label: "Settings" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 pb-[max(0.9rem,env(safe-area-inset-bottom))] pt-3">
      <div className="mx-auto max-w-lg px-4">
        <div className="grid grid-cols-4 gap-2 rounded-[1.75rem] border border-white/70 bg-white/92 p-2 shadow-[0_20px_45px_rgba(30,41,59,0.14)] backdrop-blur">
        {navItems.map((item) => {
          const isActive =
            item.href === "/" ? pathname === item.href : pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => {
                void trackAppShellNavigationUsed(item.href, { source: "bottom_nav" });
              }}
              className={`rounded-2xl px-3 py-2.5 text-center text-sm font-semibold transition ${
                isActive
                  ? "bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] text-white shadow-[0_14px_28px_rgba(79,70,229,0.24)]"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
        </div>
      </div>
    </nav>
  );
}
