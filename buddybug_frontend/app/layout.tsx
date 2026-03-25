import type { ReactNode } from "react";
import type { Metadata, Viewport } from "next";

import { AppShell } from "@/components/AppShell";
import { APP_NAME } from "@/lib/app-config";
import { AuthProvider } from "@/context/AuthContext";
import { ChildProfileProvider } from "@/context/ChildProfileContext";
import { ConnectivityProvider } from "@/context/ConnectivityContext";
import { FeatureFlagsProvider } from "@/context/FeatureFlagsContext";
import { LocaleProvider } from "@/context/LocaleContext";
import { OnboardingProvider } from "@/context/OnboardingContext";
import { ParentalControlsProvider } from "@/context/ParentalControlsContext";

import "./globals.css";

export const metadata: Metadata = {
  title: APP_NAME,
  description: "Installable bedtime story reading with saved-library favourites for families.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Buddybug",
  },
  icons: {
    apple: "/icons/apple-touch-icon.svg",
    icon: ["/icons/icon-192.svg", "/icons/icon-512.svg"],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#c7d2fe",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ConnectivityProvider>
            <LocaleProvider>
              <ChildProfileProvider>
                <OnboardingProvider>
                  <FeatureFlagsProvider>
                    <ParentalControlsProvider>
                      <AppShell>{children}</AppShell>
                    </ParentalControlsProvider>
                  </FeatureFlagsProvider>
                </OnboardingProvider>
              </ChildProfileProvider>
            </LocaleProvider>
          </ConnectivityProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
