"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { StoryQualityCard } from "@/components/StoryQualityCard";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { StoryQualityQueueItemResponse } from "@/lib/types";

export default function AdminStoryQualityPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<StoryQualityQueueItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadQueue() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<StoryQualityQueueItemResponse[]>("/admin/story-quality/review-queue", { token });
      setItems(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load the story quality review queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadQueue();
  }, [token]);

  if (loading) {
    return <LoadingState message="Loading story quality review queue..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load story quality queue" description={error} />;
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">AI story quality review queue</h2>
          <p className="mt-1 text-sm text-slate-600">
            Drafts land here when automated story or illustration checks spot quality or consistency risks.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadQueue()}
          className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
        >
          Refresh
        </button>
      </section>

      {items.length ? (
        <div className="space-y-4">
          {items.map((item) => (
            <StoryQualityCard key={item.story_id} item={item} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No stories currently need automated quality follow-up"
          description="Flagged drafts and illustration consistency warnings will appear here."
        />
      )}
    </div>
  );
}
