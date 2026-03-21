"use client";

import { AchievementBadge } from "@/components/AchievementBadge";
import type { EarnedAchievementRead } from "@/lib/types";

export function AchievementGrid({ achievements }: { achievements: EarnedAchievementRead[] }) {
  if (!achievements.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-center text-sm text-slate-600 shadow-sm">
        Achievements will appear here as story routines begin to take shape.
      </div>
    );
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {achievements.map((achievement) => (
        <AchievementBadge key={achievement.id} achievement={achievement} />
      ))}
    </div>
  );
}
