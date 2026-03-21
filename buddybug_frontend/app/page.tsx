import type { Metadata } from "next";

import { FeatureGrid } from "@/components/home/FeatureGrid";
import { HeroSection } from "@/components/home/HeroSection";
import { HomeCTA } from "@/components/home/HomeCTA";
import { HowItWorks } from "@/components/home/HowItWorks";

export const metadata: Metadata = {
  title: "Buddybug | Calm Bedtime Stories for Families",
  description:
    "A warm bedtime storytelling app with illustrated stories, narrated reading, child profiles, bedtime packs, and parental controls.",
  openGraph: {
    title: "Buddybug | Calm Bedtime Stories for Families",
    description: "Illustrated bedtime stories, narrated reading, child profiles, and bedtime packs for calmer family evenings.",
  },
};

export default function HomePage() {
  return (
    <div className="space-y-14 pb-4 md:space-y-16">
      <HeroSection />
      <HowItWorks />
      <FeatureGrid />
      <HomeCTA />
    </div>
  );
}
