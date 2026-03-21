"use client";

import { useMemo, useState } from "react";

import { useLocale } from "@/context/LocaleContext";
import { trackAudioCompleted, trackAudioStarted } from "@/lib/analytics";
import { resolveApiUrl } from "@/lib/api";
import type { ReaderAudioSummary, User } from "@/lib/types";

interface BookAudioPlayerProps {
  bookId: number;
  audioOptions: ReaderAudioSummary[];
  token?: string | null;
  user?: User | null;
}

function formatDuration(durationSeconds: number | null) {
  if (!durationSeconds) {
    return null;
  }
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = durationSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function BookAudioPlayer({ bookId, audioOptions, token, user }: BookAudioPlayerProps) {
  const { locale, t } = useLocale();
  const orderedOptions = useMemo(() => {
    return [...audioOptions].sort((a, b) => {
      const aScore = (a.is_active ? 2 : 0) + (a.approval_status === "approved" ? 1 : 0);
      const bScore = (b.is_active ? 2 : 0) + (b.approval_status === "approved" ? 1 : 0);
      return bScore - aScore;
    });
  }, [audioOptions]);

  const [selectedAudioId, setSelectedAudioId] = useState<number>(orderedOptions[0]?.id ?? 0);

  const selectedAudio =
    orderedOptions.find((option) => option.id === selectedAudioId) ?? orderedOptions[0] ?? null;

  if (!selectedAudio) {
    return null;
  }

  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/90 p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{t("listenToStory")}</h3>
        <p className="mt-1 text-sm text-slate-600">
          {selectedAudio.voice_display_name}
          {formatDuration(selectedAudio.duration_seconds)
            ? ` • ${formatDuration(selectedAudio.duration_seconds)}`
            : ""}
        </p>
      </div>

      {orderedOptions.length > 1 ? (
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">{t("voice")}</span>
          <select
            value={selectedAudio.id}
            onChange={(event) => setSelectedAudioId(Number(event.target.value))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            {orderedOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.voice_display_name}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <audio
        key={selectedAudio.id}
        controls
        preload="none"
        className="w-full"
        src={resolveApiUrl(selectedAudio.audio_url)}
        onPlay={() => {
          void trackAudioStarted(bookId, selectedAudio.voice_display_name, {
            token,
            user,
            language: locale,
          });
        }}
        onEnded={() => {
          void trackAudioCompleted(bookId, selectedAudio.voice_display_name, {
            token,
            user,
            language: locale,
          });
        }}
      >
        Your browser does not support audio playback.
      </audio>
    </section>
  );
}
