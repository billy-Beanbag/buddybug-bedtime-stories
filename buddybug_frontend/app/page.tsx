import type { Metadata } from "next";

import { PrelaunchLandingPage } from "@/components/prelaunch/PrelaunchLandingPage";
import { FeatureGrid } from "@/components/home/FeatureGrid";
import { HeroSection } from "@/components/home/HeroSection";
import { HomeCTA } from "@/components/home/HomeCTA";
import { HowItWorks } from "@/components/home/HowItWorks";
import { isPrelaunchModeEnabled } from "@/lib/prelaunch/config";

export const metadata: Metadata = {
  title: "Buddybug | Weekly Bedtime Stories Before Launch",
  description:
    "Join Buddybug before launch to receive calming bedtime stories by email each week, plus a personalised launch-day gift story.",
  openGraph: {
    title: "Buddybug | Weekly Bedtime Stories Before Launch",
    description: "A magical pre-launch signup for weekly bedtime stories delivered by private email links.",
  },
};

export default function HomePage() {
  if (isPrelaunchModeEnabled()) {
    return <PrelaunchLandingPage />;
  }

  return (
    <div className="space-y-14 pb-4 md:space-y-16">
      <HeroSection />
      <HowItWorks />
      <FeatureGrid />
      <HomeCTA />
    </div>
  );
}
