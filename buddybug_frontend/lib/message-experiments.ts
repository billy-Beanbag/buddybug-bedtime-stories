"use client";

import { apiGet } from "@/lib/api";
import { getReaderIdentifier } from "@/lib/auth";
import type { MessageExperimentBundleResponse, User } from "@/lib/types";

export const DEFAULT_MESSAGE_EXPERIMENT_BUNDLE: MessageExperimentBundleResponse = {
  homepage_cta: {
    experiment_key: "homepage_cta_copy",
    variant: "control",
    eyebrow: "Buddybug Storylight",
    headline: "Beautiful bedtime stories for children, powered by imagination.",
    description:
      "Illustrated, narrated, calming stories that grow with your family, from cozy bedtime reading to personalized daily story picks.",
    primary_cta_label: "Start Free",
    secondary_cta_label: "Explore Stories",
    pricing_cta_label: "View Pricing",
  },
  preview_wall: {
    experiment_key: "preview_wall_copy",
    variant: "control",
    title: "You’ve reached the free preview",
    description: "Upgrade to keep reading full stories, unlock narrated playback, and save favorites to your library for later.",
    primary_cta_label: "Upgrade to Premium",
    guest_primary_label: "Login to upgrade",
    guest_secondary_label: "Create account",
  },
  pricing_page: {
    experiment_key: "pricing_page_emphasis",
    variant: "control",
    headline: "Simple plans for trying Buddybug and upgrading when it clicks",
    description:
      "Start with free previews and discovery. Upgrade for full story access, narrated playback, saved-library tools, premium voices, and richer family personalization.",
    cta_headline: "Start free today and upgrade when Buddybug becomes part of your routine",
    cta_description:
      "Free is enough to explore. Premium is there when your family wants the full bedtime story experience.",
    primary_cta_label: "Start Free",
    secondary_cta_label: "Upgrade to Premium",
  },
  upgrade_card: {
    experiment_key: "premium_upgrade_card_copy",
    variant: "control",
    title: "Upgrade when Buddybug becomes part of your routine",
    description:
      "Premium unlocks full stories, narration, saved-library tools, and richer daily recommendations for your family.",
    cta_label: "Upgrade to Premium",
  },
};

export async function fetchMessageExperimentBundle({
  token,
  user,
}: {
  token?: string | null;
  user?: User | null;
}) {
  try {
    return await apiGet<MessageExperimentBundleResponse>("/message-experiments/bundle", {
      token,
      headers: {
        "X-Reader-Identifier": getReaderIdentifier(user),
      },
    });
  } catch {
    return DEFAULT_MESSAGE_EXPERIMENT_BUNDLE;
  }
}
