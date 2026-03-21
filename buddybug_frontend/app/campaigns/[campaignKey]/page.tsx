"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { DiscoveryBookCard } from "@/components/DiscoveryBookCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SeasonalBanner } from "@/components/SeasonalBanner";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet } from "@/lib/api";
import type { SeasonalCampaignDetailResponse } from "@/lib/types";

export default function CampaignDetailPage() {
  const params = useParams<{ campaignKey: string }>();
  const { token, user, isAuthenticated } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const [detail, setDetail] = useState<SeasonalCampaignDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCampaign() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiGet<SeasonalCampaignDetailResponse>(`/campaigns/${params.campaignKey}`, {
          token,
          query: {
            child_profile_id: isAuthenticated ? selectedChildProfile?.id : undefined,
          },
        });
        setDetail(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load campaign");
      } finally {
        setLoading(false);
      }
    }

    if (params.campaignKey) {
      void loadCampaign();
    }
  }, [isAuthenticated, params.campaignKey, selectedChildProfile?.id, token]);

  if (loading) {
    return <LoadingState message="Loading campaign..." />;
  }

  if (error || !detail) {
    return <EmptyState title="Campaign unavailable" description={error || "This campaign could not be loaded."} />;
  }

  return (
    <div className="space-y-5">
      <SeasonalBanner campaign={detail.campaign} surface="campaign" />
      <section className="space-y-3">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">{detail.campaign.title}</h2>
          <p className="mt-1 text-sm text-slate-600">
            {detail.campaign.description || "A themed collection of Buddybug stories for this calendar moment."}
          </p>
        </div>
        {detail.items.length ? (
          <div className="grid gap-3">
            {detail.items.map((item) => (
              <DiscoveryBookCard
                key={item.book_id}
                book={item}
                token={token}
                user={user}
                childProfileId={selectedChildProfile?.id}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No stories available right now"
            description="Try changing child profile context or check back when new seasonal stories are added."
          />
        )}
      </section>
    </div>
  );
}
