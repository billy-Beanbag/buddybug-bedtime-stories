"use client";

import { trackEvent } from "@/lib/analytics";
import { apiPatch, apiPost } from "@/lib/api";
import {
  clearPendingSyncAction,
  getPendingSyncActionCount,
  listPendingSyncActions,
  markOfflineSyncAction,
} from "@/lib/offline-storage";
import type { OfflineSyncActionRecord, OfflineSyncActionType, User } from "@/lib/types";

interface QueueSyncActionInput {
  type: OfflineSyncActionType;
  payload: Record<string, unknown>;
}

interface FlushSyncQueueOptions {
  token?: string | null;
  user?: User | null;
}

export async function queueSyncAction(type: OfflineSyncActionType, payload: Record<string, unknown>) {
  const action: OfflineSyncActionRecord = {
    type,
    payload,
    created_at: new Date().toISOString(),
  };
  return markOfflineSyncAction(action);
}

export async function flushSyncQueue(options: FlushSyncQueueOptions = {}) {
  const actions = await listPendingSyncActions();
  if (!actions.length) {
    return 0;
  }

  let flushedCount = 0;
  for (const action of actions) {
    if (!action.id) {
      continue;
    }

    try {
      if (action.type === "reading_progress") {
        await apiPost("/reader/progress", action.payload);
      } else if (action.type === "library_opened") {
        if (!options.token) {
          continue;
        }
        const payload = action.payload as { book_id?: number; child_profile_id?: number | null };
        if (!payload.book_id) {
          await clearPendingSyncAction(action.id);
          continue;
        }
        await apiPost(`/library/me/books/${payload.book_id}/opened`, undefined, {
          token: options.token,
          query: { child_profile_id: payload.child_profile_id ?? undefined },
        });
      } else if (action.type === "library_offline_state") {
        if (!options.token) {
          continue;
        }
        const payload = action.payload as {
          book_id?: number;
          child_profile_id?: number | null;
          saved_for_offline?: boolean;
        };
        if (!payload.book_id) {
          await clearPendingSyncAction(action.id);
          continue;
        }
        await apiPatch(
          `/library/me/books/${payload.book_id}`,
          { saved_for_offline: payload.saved_for_offline ?? false },
          {
            token: options.token,
            query: { child_profile_id: payload.child_profile_id ?? undefined },
          },
        );
      }

      await clearPendingSyncAction(action.id);
      flushedCount += 1;
    } catch {
      // Keep remaining actions queued for the next reconnect.
      break;
    }
  }

  if (flushedCount > 0) {
    void trackEvent(
      {
        event_name: "offline_sync_flushed",
        metadata: { flushed_count: flushedCount },
      },
      { token: options.token, user: options.user },
    );
  }

  return flushedCount;
}

export function getSyncQueueLength() {
  return getPendingSyncActionCount();
}
