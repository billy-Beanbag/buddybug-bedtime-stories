import type { Metadata } from "next";

import { PricingPageContent } from "@/components/marketing/PricingPageContent";

export const metadata: Metadata = {
  title: "Buddybug Pricing | Free Plan and Premium",
  description:
    "Compare Buddybug Free Plan and Premium for weekly stories, full library access, bedtime packs, narration voices, saved-library tools, child profiles, and personalised recommendations.",
  openGraph: {
    title: "Buddybug Pricing",
    description:
      "Compare the Buddybug Free Plan and Premium, including saved-library tools, for families building better bedtime routines.",
  },
};

export default function PricingPage() {
  return <PricingPageContent />;
}
