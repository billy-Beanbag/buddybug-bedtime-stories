import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type {
  DailyStorySuggestionResponse,
  NotificationEventRead,
  NotificationPreferenceRead,
} from "@/lib/types";

export function fetchNotifications({
  token,
  unreadOnly,
  limit,
}: {
  token: string;
  unreadOnly?: boolean;
  limit?: number;
}) {
  return apiGet<{ items: NotificationEventRead[] }>("/notifications/me", {
    token,
    query: { unread_only: unreadOnly, limit },
  });
}

export function fetchNotificationPreferences({ token }: { token: string }) {
  return apiGet<NotificationPreferenceRead>("/notifications/preferences/me", { token });
}

export function updateNotificationPreferences({
  token,
  payload,
}: {
  token: string;
  payload: Partial<NotificationPreferenceRead>;
}) {
  return apiPatch<NotificationPreferenceRead>("/notifications/preferences/me", payload, { token });
}

export function fetchDailyStory({
  token,
  childProfileId,
  date,
}: {
  token: string;
  childProfileId?: number | null;
  date?: string;
}) {
  return apiGet<DailyStorySuggestionResponse>("/notifications/me/daily-story", {
    token,
    query: { child_profile_id: childProfileId, date },
  });
}

export function markNotificationRead({
  token,
  notificationId,
  isRead,
}: {
  token: string;
  notificationId: number;
  isRead: boolean;
}) {
  return apiPatch<NotificationEventRead>(`/notifications/me/${notificationId}`, { is_read: isRead }, { token });
}

export function markAllNotificationsRead({ token }: { token: string }) {
  return apiPost<{ ok: boolean; updated_count: number }>("/notifications/me/mark-all-read", undefined, { token });
}
