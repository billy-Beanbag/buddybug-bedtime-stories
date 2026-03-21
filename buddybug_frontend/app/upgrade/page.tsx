import type { Metadata } from "next";

import { UpgradePageContent } from "@/components/upgrade/UpgradePageContent";

export const metadata: Metadata = {
  title: "Upgrade | Buddybug Premium",
  description:
    "Compare the Buddybug Free Plan and Premium, including downloadable offline stories, then upgrade whenever your family is ready.",
  openGraph: {
    title: "Upgrade to Buddybug Premium",
    description: "A clear in-app comparison of the Buddybug Free Plan and Premium, including downloadable offline stories.",
  },
};

export default function UpgradePage() {
  return <UpgradePageContent />;
}
