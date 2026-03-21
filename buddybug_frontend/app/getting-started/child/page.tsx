import type { Metadata } from "next";

import { GettingStartedChildSetup } from "@/components/GettingStartedChildSetup";

export const metadata: Metadata = {
  title: "Child Setup | Buddybug",
  description: "Create or confirm a child profile so Buddybug can personalise reading and recommendations.",
};

export default function GettingStartedChildPage() {
  return <GettingStartedChildSetup />;
}
