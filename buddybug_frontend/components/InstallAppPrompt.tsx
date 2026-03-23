"use client";

import { useEffect, useState } from "react";

import { trackEvent } from "@/lib/analytics";
import { ENABLE_INSTALL_PROMPT } from "@/lib/app-config";

const INSTALL_DISMISS_KEY = "buddybug.install.dismissed";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

export function InstallAppPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!ENABLE_INSTALL_PROMPT) {
      return;
    }
    if (typeof window === "undefined") {
      return;
    }
    const isDismissed = window.localStorage.getItem(INSTALL_DISMISS_KEY) === "true";
    setDismissed(isDismissed);

    function handleBeforeInstallPrompt(event: Event) {
      // If the user already dismissed this prompt, we should not prevent the native
      // banner (otherwise Chrome logs a warning because `prompt()` will never be called).
      if (isDismissed) {
        return;
      }
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
    }

    function handleAppInstalled() {
      setDeferredPrompt(null);
      setDismissed(true);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(INSTALL_DISMISS_KEY, "true");
      }
      void trackEvent({
        event_name: "pwa_installed",
        metadata: { source: "install_prompt" },
      });
    }

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  if (!ENABLE_INSTALL_PROMPT || !deferredPrompt || dismissed) {
    return null;
  }

  return (
    <div className="mb-4 rounded-3xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-900 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-medium">Install Buddybug</p>
          <p className="mt-1 text-indigo-800">Add Buddybug to your home screen for a more app-like bedtime reading flow.</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => {
              setDismissed(true);
              window.localStorage.setItem(INSTALL_DISMISS_KEY, "true");
            }}
            className="rounded-2xl border border-indigo-200 bg-white px-3 py-2 font-medium text-indigo-900"
          >
            Not now
          </button>
          <button
            type="button"
            onClick={() => {
              void deferredPrompt.prompt();
              void deferredPrompt.userChoice.finally(() => setDeferredPrompt(null));
            }}
            className="rounded-2xl bg-slate-900 px-3 py-2 font-medium text-white"
          >
            Install
          </button>
        </div>
      </div>
    </div>
  );
}
