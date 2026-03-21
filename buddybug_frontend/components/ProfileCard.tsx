"use client";

import type { User } from "@/lib/types";
import { useLocale } from "@/context/LocaleContext";

interface ProfileCardProps {
  user: User;
}

export function ProfileCard({ user }: ProfileCardProps) {
  const { t } = useLocale();

  return (
    <section className="relative space-y-4 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
      <div className="relative space-y-4">
      <div>
        <h2 className="text-2xl font-semibold text-white">{t("profileTitle")}</h2>
        <p className="mt-1 text-sm text-indigo-100">{t("profileDescription")}</p>
      </div>

      <dl className="grid gap-3 text-sm">
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <dt className="text-indigo-200">{t("email")}</dt>
          <dd className="mt-1 font-medium text-white">{user.email}</dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <dt className="text-indigo-200">{t("displayName")}</dt>
          <dd className="mt-1 font-medium text-white">{user.display_name || t("notSet")}</dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <dt className="text-indigo-200">{t("country")}</dt>
          <dd className="mt-1 font-medium text-white">{user.country || t("notSet")}</dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <dt className="text-indigo-200">{t("language")}</dt>
          <dd className="mt-1 font-medium text-white">{user.language}</dd>
        </div>
      </dl>
      </div>
    </section>
  );
}
