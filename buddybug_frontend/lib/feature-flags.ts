"use client";

import { apiGet } from "@/lib/api";
import { getReaderIdentifier } from "@/lib/auth";
import type { FeatureFlagBundleResponse, User } from "@/lib/types";

export const EMPTY_FEATURE_FLAG_BUNDLE: FeatureFlagBundleResponse = {
  flags: {},
};

interface FetchFeatureFlagBundleOptions {
  token?: string | null;
  user?: User | null;
  childProfileId?: number | null;
  language?: string | null;
}

export async function fetchFeatureFlagBundle({
  token,
  user,
  childProfileId,
  language,
}: FetchFeatureFlagBundleOptions): Promise<FeatureFlagBundleResponse> {
  return apiGet<FeatureFlagBundleResponse>("/feature-flags/bundle", {
    token,
    headers: {
      "X-Reader-Identifier": getReaderIdentifier(user),
    },
    query: {
      child_profile_id: childProfileId ?? undefined,
      language: language || undefined,
    },
  });
}
