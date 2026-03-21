"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { NotificationList } from "@/components/NotificationList";
import { NotificationPreferencesForm } from "@/components/NotificationPreferencesForm";
import { useAuth } from "@/context/AuthContext";
import {
  fetchNotificationPreferences,
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  updateNotificationPreferences,
} from "@/lib/notifications";
import type { NotificationEventRead, NotificationPreferenceRead } from "@/lib/types";

export default function NotificationsPage() {
  const { isAuthenticated, token, isLoading } = useAuth();
  const [items, setItems] = useState<NotificationEventRead[]>([]);
  const [preference, setPreference] = useState<NotificationPreferenceRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadState() {
      if (!isAuthenticated || !token) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const [notificationsResponse, preferenceResponse] = await Promise.all([
          fetchNotifications({ token, limit: 100 }),
          fetchNotificationPreferences({ token }),
        ]);
        setItems(notificationsResponse.items);
        setPreference(preferenceResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load notifications");
      } finally {
        setLoading(false);
      }
    }

    void loadState();
  }, [isAuthenticated, token]);

  if (isLoading || loading) {
    return <LoadingState message="Loading notifications..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Notifications are available after login"
          description="Sign in to view reminders and daily story delivery."
        />
        <Link
          href="/login"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          Log in
        </Link>
      </div>
    );
  }

  if (error) {
    return <EmptyState title="Unable to load notifications" description={error} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Notifications</h2>
          <p className="mt-1 text-sm text-slate-600">In-app reminders and story updates for your family.</p>
        </div>
        <button
          type="button"
          onClick={() =>
            void markAllNotificationsRead({ token }).then(() =>
              setItems((current) => current.map((item) => ({ ...item, is_read: true }))),
            )
          }
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Mark all read
        </button>
      </div>

      <NotificationList
        items={items}
        onToggleRead={async (item) => {
          const updated = await markNotificationRead({
            token,
            notificationId: item.id,
            isRead: !item.is_read,
          });
          setItems((current) => current.map((row) => (row.id === updated.id ? updated : row)));
        }}
      />

      {preference ? (
        <NotificationPreferencesForm
          preference={preference}
          onSave={async (payload) => {
            const updated = await updateNotificationPreferences({ token, payload });
            setPreference(updated);
          }}
        />
      ) : null}
    </div>
  );
}
