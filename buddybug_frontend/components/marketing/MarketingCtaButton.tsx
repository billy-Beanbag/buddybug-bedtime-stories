"use client";

import Link from "next/link";

import { useAuth } from "@/context/AuthContext";
import { trackMarketingCtaClicked } from "@/lib/analytics";

type CtaKind = "start-free" | "upgrade" | "explore" | "pricing" | "login" | "open-app";

function resolveHref(kind: CtaKind, isAuthenticated: boolean) {
  switch (kind) {
    case "start-free":
      return isAuthenticated ? "/library" : "/register/free";
    case "upgrade":
      return isAuthenticated ? "/upgrade" : "/register/premium";
    case "explore":
      return "/library";
    case "pricing":
      return isAuthenticated ? "/upgrade" : "/pricing";
    case "login":
      return isAuthenticated ? "/library" : "/login";
    case "open-app":
      return "/library";
    default:
      return "/";
  }
}

export function MarketingCtaButton({
  kind,
  label,
  source,
  variant = "primary",
  className = "",
  onClick,
  href,
}: {
  kind: CtaKind;
  label: string;
  source: string;
  variant?: "primary" | "secondary" | "ghost";
  className?: string;
  onClick?: () => void;
  href?: string;
}) {
  const { isAuthenticated, token, user } = useAuth();
  const resolvedHref = href || resolveHref(kind, isAuthenticated);
  const variantClassName =
    variant === "primary"
      ? "bg-slate-900 text-white"
      : variant === "secondary"
        ? "border border-slate-200 bg-white text-slate-900"
        : "text-slate-700 underline-offset-4 hover:underline";

  return (
    <Link
      href={resolvedHref}
      onClick={() => {
        onClick?.();
        void trackMarketingCtaClicked({
          token,
          user,
          source,
          target: resolvedHref,
          ctaLabel: label,
        });
      }}
      className={`inline-flex items-center justify-center rounded-2xl px-5 py-3 text-sm font-medium transition hover:-translate-y-0.5 ${variantClassName} ${className}`}
    >
      {label}
    </Link>
  );
}
