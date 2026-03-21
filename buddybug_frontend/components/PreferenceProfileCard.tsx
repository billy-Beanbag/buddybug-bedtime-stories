import type { UserStoryProfileRead } from "@/lib/types";

interface PreferenceProfileCardProps {
  profile: UserStoryProfileRead | null;
  rebuilding?: boolean;
  onRebuild?: () => void;
}

function displayValue(value: string | null) {
  return value || "Not enough feedback yet";
}

export function PreferenceProfileCard({
  profile,
  rebuilding = false,
  onRebuild,
}: PreferenceProfileCardProps) {
  return (
    <section className="relative space-y-4 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
      <div className="relative space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold text-white">Preference profile</h3>
          <p className="mt-1 text-sm text-indigo-100">A lightweight summary of your evolving story tastes.</p>
        </div>
        {onRebuild ? (
          <button
            type="button"
            onClick={onRebuild}
            disabled={rebuilding}
            className="rounded-2xl border border-white/15 bg-white/10 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {rebuilding ? "Rebuilding..." : "Rebuild profile"}
          </button>
        ) : null}
      </div>

      <div className="grid gap-3 text-sm">
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-indigo-200">Favorite characters</p>
          <p className="mt-1 font-medium text-white">{displayValue(profile?.favorite_characters || null)}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-indigo-200">Preferred tones</p>
          <p className="mt-1 font-medium text-white">{displayValue(profile?.preferred_tones || null)}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
          <p className="text-indigo-200">Preferred styles</p>
          <p className="mt-1 font-medium text-white">{displayValue(profile?.preferred_styles || null)}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-4 text-center text-white">
          <p className="text-xs uppercase tracking-wide text-indigo-200">Rated</p>
          <p className="mt-1 text-2xl font-semibold">{profile?.total_books_rated ?? 0}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-4 text-center text-white">
          <p className="text-xs uppercase tracking-wide text-indigo-200">Completed</p>
          <p className="mt-1 text-2xl font-semibold">{profile?.total_books_completed ?? 0}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-4 text-center text-white">
          <p className="text-xs uppercase tracking-wide text-indigo-200">Replayed</p>
          <p className="mt-1 text-2xl font-semibold">{profile?.total_books_replayed ?? 0}</p>
        </div>
      </div>
      </div>
    </section>
  );
}
