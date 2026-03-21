"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { fetchNotifications } from "@/lib/notifications";

export function NotificationBell() {
  const { isAuthenticated, token } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setUnreadCount(0);
      return;
    }
    void fetchNotifications({ token, unreadOnly: true, limit: 50 })
      .then((response) => setUnreadCount(response.items.length))
      .catch(() => setUnreadCount(0));
  }, [isAuthenticated, token]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Link
      href="/notifications"
      className="relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-sm font-medium text-slate-900"
      aria-label="Notifications"
    >
      <span>N</span>
      {unreadCount ? (
        <span className="absolute -right-1 -top-1 inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-semibold text-white">
          {unreadCount}
        </span>
      ) : null}
    </Link>
  );
}
