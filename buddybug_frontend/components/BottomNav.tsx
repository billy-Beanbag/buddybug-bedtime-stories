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
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200/80 bg-white/95 backdrop-blur supports-[padding:max(0px)]:pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      <div className="mx-auto grid max-w-md grid-cols-4 gap-2 px-4 py-3">
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
              className={`rounded-2xl px-3 py-2 text-center text-sm font-medium transition ${
                isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
