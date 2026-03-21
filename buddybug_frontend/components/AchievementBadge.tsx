"use client";

import type { EarnedAchievementRead } from "@/lib/types";

function iconLabel(iconKey: string | null) {
  switch (iconKey) {
    case "storybook_star":
      return "Story";
    case "moon_stack":
      return "Moon";
    case "calendar_glow":
      return "Week";
    case "bookmark_heart":
      return "Saved";
    case "sparkle_speaker":
      return "Audio";
    case "moon_path":
      return "Calm";
    case "library_shelf":
      return "Shelf";
    default:
      return "Badge";
  }
}

export function AchievementBadge({ achievement }: { achievement: EarnedAchievementRead }) {
  return (
    <article className="rounded-[2rem] border border-white/70 bg-white/85 p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-xs font-semibold text-indigo-700">
          {iconLabel(achievement.icon_key)}
        </div>
        <div className="min-w-0">
          <p className="text-lg font-semibold text-slate-900">{achievement.title || "Achievement earned"}</p>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {achievement.description || "A gentle Buddybug milestone was earned."}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {achievement.child_profile_id ? "Child milestone" : "Family milestone"}
            </span>
            <span>Earned {new Date(achievement.earned_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </article>
  );
}
