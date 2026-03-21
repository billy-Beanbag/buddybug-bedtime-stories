import type { Metadata } from "next";

import { GettingStartedPageContent } from "@/components/GettingStartedPageContent";

export const metadata: Metadata = {
  title: "Getting Started | Buddybug",
  description: "Learn what Buddybug can do, then set up a child profile to begin reading.",
};

export default function GettingStartedPage() {
  return <GettingStartedPageContent />;
}
