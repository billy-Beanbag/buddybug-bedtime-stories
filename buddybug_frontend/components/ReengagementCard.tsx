"use client";

import Link from "next/link";

import type { ReengagementSuggestionRead } from "@/lib/types";

interface ReengagementCardProps {
  suggestion: ReengagementSuggestionRead;
  compact?: boolean;
  dismissing?: boolean;
  onDismiss: (suggestionId: number) => void;
}

const TYPE_LABELS: Record<string, string> = {
  continue_story: "Continue reading",
  revisit_saved_story: "Saved story reminder",
  daily_pick_return: "Tonight's return pick",
  premium_upgrade_reminder: "Premium value",
  lapsed_premium_return: "Premium comeback",
  child_profile_setup_reminder: "Family setup",
};

function getSuggestionAction(suggestion: ReengagementSuggestionRead) {
  switch (suggestion.suggestion_type) {
    case "continue_story":
      return {
        href: suggestion.related_book_id ? `/reader/${suggestion.related_book_id}` : "/library",
        label: "Continue reading",
      };
    case "revisit_saved_story":
      return {
        href: "/saved",
        label: "Open saved stories",
      };
    case "daily_pick_return":
      return {
        href: suggestion.related_book_id ? `/reader/${suggestion.related_book_id}` : "/library",
        label: "Read tonight's pick",
      };
    case "premium_upgrade_reminder":
      return {
        href: "/pricing",
        label: "View premium",
      };
    case "lapsed_premium_return":
      return {
        href: "/pricing",
        label: "Return to premium",
      };
    case "child_profile_setup_reminder":
      return {
        href: "/children",
        label: "Create child profile",
      };
    default:
      return {
        href: "/library",
        label: "Open Buddybug",
      };
  }
}

export function ReengagementCard({ suggestion, compact = false, dismissing = false, onDismiss }: ReengagementCardProps) {
  const action = getSuggestionAction(suggestion);

  return (
    <article
      className={`rounded-[2rem] border border-amber-100 bg-white/90 shadow-sm ${
        compact ? "p-4" : "p-5"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-amber-700">
            {TYPE_LABELS[suggestion.suggestion_type] || "Come back to Buddybug"}
          </p>
          <h3 className={`mt-2 font-semibold text-slate-900 ${compact ? "text-lg" : "text-xl"}`}>{suggestion.title}</h3>
        </div>
        <button
          type="button"
          onClick={() => onDismiss(suggestion.id)}
          disabled={dismissing}
          className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 disabled:opacity-60"
        >
          {dismissing ? "Hiding..." : "Dismiss"}
        </button>
      </div>
      <p className={`mt-3 text-slate-600 ${compact ? "text-sm leading-6" : "text-sm leading-6"}`}>{suggestion.body}</p>
      <Link
        href={action.href}
        className="mt-4 inline-flex rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-medium text-white hover:bg-indigo-500"
      >
        {action.label}
      </Link>
    </article>
  );
}
