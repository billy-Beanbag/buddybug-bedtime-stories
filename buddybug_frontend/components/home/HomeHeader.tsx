"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/context/AuthContext";

export function HomeHeader() {
  const pathname = usePathname();
  const { isAuthenticated, isLoading } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const navItems = useMemo(
    () => [
      { href: "/", label: "Home" },
      { href: "/library", label: "Library" },
      { href: "/children", label: "Children" },
      { href: "/bedtime-pack", label: "Bedtime Pack" },
      isAuthenticated ? { href: "/upgrade", label: "Upgrade" } : { href: "/pricing", label: "Pricing" },
    ],
    [isAuthenticated],
  );

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-20 border-b border-indigo-100/60 bg-[rgba(246,245,255,0.82)] backdrop-blur-xl">
      <div className="mx-auto max-w-6xl px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-3 text-slate-900">
            <span className="relative flex h-11 w-11 items-center justify-center overflow-hidden rounded-full border border-white/70 bg-[radial-gradient(circle_at_30%_30%,_#fff7d6,_#f4d57b_40%,_#7c86ff)] shadow-[0_0_30px_rgba(124,134,255,0.25)]">
              <Image
                src="/home/buddybug-mark.png"
                alt="Buddybug logo"
                fill
                sizes="44px"
                className="object-cover"
                priority
              />
            </span>
            <span>
              <span className="block text-lg font-semibold tracking-tight">Buddybug</span>
              <span className="block text-xs uppercase tracking-[0.22em] text-slate-500">Storylight bedtime</span>
            </span>
          </Link>

          <button
            type="button"
            onClick={() => setMenuOpen((current) => !current)}
            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white/90 px-3 py-2 text-sm font-medium text-slate-900 shadow-sm"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            <span className="flex flex-col gap-1">
              <span className="block h-0.5 w-5 rounded-full bg-slate-900" />
              <span className="block h-0.5 w-5 rounded-full bg-slate-900" />
              <span className="block h-0.5 w-5 rounded-full bg-slate-900" />
            </span>
          </button>
        </div>

        {menuOpen ? (
          <div className="mt-4 space-y-4 border-t border-indigo-100/80 pt-4">
            <nav className="grid gap-2">
            {navItems.map((item) => {
              const isActive =
                item.href === "/" ? pathname === item.href : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-2xl px-4 py-3 text-center text-sm font-medium transition ${
                    isActive
                      ? "border border-indigo-200 bg-indigo-50 text-indigo-950"
                      : "border border-slate-200 bg-white text-slate-900 hover:bg-white/80"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
            </nav>

            <nav className="grid gap-2">
            <Link
              href={isAuthenticated ? "/profile" : "/login"}
              className={`rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900 shadow-sm transition hover:border-slate-300 hover:bg-white ${
                pathname === "/profile" || pathname === "/login"
                  ? "border-indigo-200 bg-indigo-50 text-indigo-950"
                  : ""
              }`}
            >
              {isLoading ? "Account" : isAuthenticated ? "Profile" : "Login"}
            </Link>
          </nav>
          </div>
        ) : null}
      </div>
    </header>
  );
}
