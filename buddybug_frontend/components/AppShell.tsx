"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { AppTopBar } from "@/components/AppTopBar";
import { BottomNav } from "@/components/BottomNav";
import { InstallAppPrompt } from "@/components/InstallAppPrompt";
import { MarketingFooter } from "@/components/marketing/MarketingFooter";
import { MarketingHeader } from "@/components/marketing/MarketingHeader";
import { OfflineStatusBanner } from "@/components/OfflineStatusBanner";
import { PrelaunchShell } from "@/components/prelaunch/PrelaunchShell";
import { isPrelaunchModeEnabled, isPrelaunchPublicPath } from "@/lib/prelaunch/config";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAdminRoute = pathname.startsWith("/admin");
  const isReaderRoute = pathname.startsWith("/reader/");
  const isOnboardingRoute = pathname.startsWith("/onboarding");
  const isLoginRoute = pathname === "/login";
  const isRegisterRoute = pathname.startsWith("/register");
  const isGettingStartedRoute = pathname.startsWith("/getting-started");
  const isPricingRoute = pathname === "/pricing";
  const isMarketingRoute = ["/", "/features", "/pricing", "/how-it-works", "/for-parents", "/faq", "/status"].includes(pathname);
  const isPrelaunchPublicRoute = isPrelaunchModeEnabled() && isPrelaunchPublicPath(pathname);

  if (isAdminRoute) {
    return <div className="min-h-screen bg-slate-100 text-slate-900">{children}</div>;
  }

  if (isPrelaunchPublicRoute) {
    return <PrelaunchShell>{children}</PrelaunchShell>;
  }

  if (isMarketingRoute) {
    return (
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.97),_rgba(238,242,255,0.9)_42%,_rgba(224,231,255,0.82))] text-slate-900">
        {!isPricingRoute ? <MarketingHeader /> : null}
        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 md:py-10">{children}</main>
        {!isPricingRoute ? <MarketingFooter /> : null}
      </div>
    );
  }

  if (isOnboardingRoute) {
    return (
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.97),_rgba(238,242,255,0.9)_42%,_rgba(224,231,255,0.82))] text-slate-900">
        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 md:py-10">{children}</main>
      </div>
    );
  }

  if (isReaderRoute) {
    return (
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.95),_rgba(238,242,255,0.9)_45%,_rgba(224,231,255,0.85))] text-slate-900">
        <div className="mx-auto min-h-screen max-w-7xl px-3 py-3 sm:px-4 sm:py-4 lg:px-6">
          <InstallAppPrompt />
          <OfflineStatusBanner />
          <main className="min-h-[calc(100vh-2rem)]">{children}</main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.95),_rgba(238,242,255,0.9)_45%,_rgba(224,231,255,0.85))] text-slate-900">
      <div className="mx-auto min-h-screen max-w-4xl px-4 pb-28 pt-4 sm:px-6 lg:px-8">
        <InstallAppPrompt />
        <OfflineStatusBanner />
        {!isOnboardingRoute && !isLoginRoute && !isRegisterRoute && !isGettingStartedRoute ? <AppTopBar /> : null}
        <main className="pb-2">{children}</main>
      </div>
      {!isOnboardingRoute && !isLoginRoute && !isRegisterRoute && !isGettingStartedRoute ? <BottomNav /> : null}
    </div>
  );
}
