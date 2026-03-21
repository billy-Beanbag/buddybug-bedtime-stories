"use client";

import { trackDiscoveryCollectionOpened } from "@/lib/analytics";
import type { BookCollectionRead, User } from "@/lib/types";

export function CollectionCarousel({
  collections,
  onSelect,
  token,
  user,
  childProfileId,
}: {
  collections: BookCollectionRead[];
  onSelect: (collection: BookCollectionRead) => void;
  token?: string | null;
  user?: User | null;
  childProfileId?: number | null;
}) {
  if (!collections.length) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-3 overflow-x-auto pb-1">
        {collections.map((collection) => (
          <button
            key={collection.id}
            type="button"
            onClick={() => {
              void trackDiscoveryCollectionOpened(collection.key, {
                token,
                user,
                childProfileId,
                language: collection.language || undefined,
                source: "collection_carousel",
              });
              onSelect(collection);
            }}
            className="min-w-[220px] rounded-3xl border border-white/70 bg-white/85 p-4 text-left shadow-sm"
          >
            <p className="text-sm font-semibold text-slate-900">{collection.title}</p>
            <p className="mt-2 text-sm text-slate-600">{collection.description || "Curated collection"}</p>
            <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">
              {collection.language?.toUpperCase() || "All languages"} {collection.age_band ? `• ${collection.age_band}` : ""}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
