"use client";

import { IS_WRAPPED_APP } from "@/lib/app-config";

export function isBrowser() {
  return typeof window !== "undefined";
}

export function isStandalonePWA() {
  if (!isBrowser()) {
    return false;
  }
  return (
    window.matchMedia?.("(display-mode: standalone)").matches ||
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

export function isWrappedApp() {
  return IS_WRAPPED_APP;
}

export function getPlatformLabel() {
  if (isWrappedApp()) {
    return "Wrapped app";
  }
  if (isStandalonePWA()) {
    return "Installed PWA";
  }
  return "Web app";
}
