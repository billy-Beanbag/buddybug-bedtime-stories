"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { StatusComponentList } from "@/components/status/StatusComponentList";
import { StatusHero } from "@/components/status/StatusHero";
import { StatusNoticeList } from "@/components/status/StatusNoticeList";
import { apiGet } from "@/lib/api";
import type { PublicStatusPageResponse } from "@/lib/types";

export default function PublicStatusPage() {
  const [statusPage, setStatusPage] = useState<PublicStatusPageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    void apiGet<PublicStatusPageResponse>("/status")
      .then((response) => setStatusPage(response))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load service status"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <LoadingState message="Loading service status..." />;
  }

  if (error || !statusPage) {
    return <EmptyState title="Unable to load Buddybug status" description={error || "Status data is unavailable right now."} />;
  }

  return (
    <div className="space-y-8 md:space-y-10">
      <StatusHero overallStatus={statusPage.overall_status} />
      <StatusComponentList components={statusPage.components} />
      <div className="grid gap-6 xl:grid-cols-2">
        <StatusNoticeList
          title="Active notices"
          description="Current customer-facing incidents and important service notices."
          notices={statusPage.active_notices}
          emptyTitle="No active customer-facing notices at the moment."
        />
        <StatusNoticeList
          title="Upcoming maintenance"
          description="Planned service windows that may affect parts of Buddybug."
          notices={statusPage.upcoming_maintenance}
          emptyTitle="No scheduled maintenance is currently planned."
        />
      </div>
    </div>
  );
}
