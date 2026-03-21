"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { trackAudioCompleted, trackAudioStarted, trackAutoplayBlockedByParentalControls } from "@/lib/analytics";
import { resolveApiUrl } from "@/lib/api";
import type {
  NarrationSegmentRead,
  NarrationVoiceRead,
  ReaderNarrationResponse,
  ResolvedParentalControlsResponse,
  User,
} from "@/lib/types";

import { VoiceSelector } from "./VoiceSelector";

interface StoryAudioPlayerProps {
  bookId: number;
  narration: ReaderNarrationResponse;
  voices: NarrationVoiceRead[];
  currentPageNumber: number;
  onPageChange: (pageNumber: number) => void;
  onVoiceChange: (voiceKey: string) => void;
  token?: string | null;
  user?: User | null;
  language?: string;
  childProfileId?: number | null;
  resolvedControls?: ResolvedParentalControlsResponse | null;
}

function formatDuration(durationSeconds: number | null) {
  if (!durationSeconds) {
    return null;
  }
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = durationSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function StoryAudioPlayer({
  bookId,
  narration,
  voices,
  currentPageNumber,
  onPageChange,
  onVoiceChange,
  token,
  user,
  language,
  childProfileId,
  resolvedControls,
}: StoryAudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const shouldResumeAfterAdvance = useRef(false);
  const [enabled, setEnabled] = useState(true);
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [progressPercent, setProgressPercent] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const orderedSegments = useMemo(() => {
    return [...narration.segments].sort((a, b) => a.page_number - b.page_number);
  }, [narration.segments]);

  const currentSegment: NarrationSegmentRead | null = orderedSegments[segmentIndex] ?? null;

  useEffect(() => {
    const matchedIndex = orderedSegments.findIndex((segment) => segment.page_number === currentPageNumber);
    if (matchedIndex >= 0 && matchedIndex !== segmentIndex) {
      setSegmentIndex(matchedIndex);
    }
  }, [currentPageNumber, orderedSegments, segmentIndex]);

  useEffect(() => {
    if (!currentSegment || !audioRef.current) {
      return;
    }
    audioRef.current.src = resolveApiUrl(currentSegment.audio_url);
    audioRef.current.load();
    setProgressPercent(0);
    if (enabled && shouldResumeAfterAdvance.current && resolvedControls?.allow_audio_autoplay) {
      void audioRef.current.play().catch(() => undefined);
    }
    shouldResumeAfterAdvance.current = false;
  }, [currentSegment, enabled, resolvedControls?.allow_audio_autoplay]);

  useEffect(() => {
    if (resolvedControls && !resolvedControls.allow_audio_autoplay) {
      void trackAutoplayBlockedByParentalControls(bookId, {
        token,
        user,
        language,
        childProfileId,
      });
    }
  }, [bookId, childProfileId, language, resolvedControls, token, user]);

  if (!currentSegment) {
    return null;
  }

  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/90 p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Narrated story</h3>
          <p className="mt-1 text-sm text-slate-600">
            {narration.voice.display_name}
            {formatDuration(narration.narration.duration_seconds)
              ? ` • ${formatDuration(narration.narration.duration_seconds)}`
              : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setEnabled((current) => {
              const next = !current;
              if (!next) {
                audioRef.current?.pause();
              }
              return next;
            });
          }}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900"
        >
          {enabled ? "Narration on" : "Narration off"}
        </button>
      </div>

      <VoiceSelector
        voices={voices}
        selectedVoiceKey={narration.voice.key}
        onChange={(voiceKey) => {
          audioRef.current?.pause();
          setIsPlaying(false);
          onVoiceChange(voiceKey);
        }}
      />

      <div className="rounded-2xl bg-slate-50 px-4 py-3">
        <div className="mb-2 flex items-center justify-between text-sm text-slate-600">
          <span>Page {currentSegment.page_number}</span>
          <span>{Math.round(progressPercent)}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-200">
          <div className="h-full rounded-full bg-indigo-500 transition-all" style={{ width: `${progressPercent}%` }} />
        </div>
      </div>

      <audio
        ref={audioRef}
        controls
        autoPlay={Boolean(resolvedControls?.allow_audio_autoplay && enabled)}
        preload="metadata"
        className="w-full"
        src={resolveApiUrl(currentSegment.audio_url)}
        onPlay={() => {
          setIsPlaying(true);
          void trackAudioStarted(bookId, narration.voice.display_name, {
            token,
            user,
            language,
            childProfileId,
          });
        }}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={() => {
          if (!audioRef.current || !audioRef.current.duration) {
            setProgressPercent(0);
            return;
          }
          setProgressPercent((audioRef.current.currentTime / audioRef.current.duration) * 100);
        }}
        onEnded={() => {
          setIsPlaying(false);
          setProgressPercent(100);
          void trackAudioCompleted(bookId, narration.voice.display_name, {
            token,
            user,
            language,
            childProfileId,
          });
          const nextIndex = segmentIndex + 1;
          const nextSegment = orderedSegments[nextIndex];
          if (!enabled || !nextSegment) {
            return;
          }
          shouldResumeAfterAdvance.current = Boolean(resolvedControls?.allow_audio_autoplay);
          setSegmentIndex(nextIndex);
          onPageChange(nextSegment.page_number);
        }}
      >
        Your browser does not support audio playback.
      </audio>

      <p className="text-xs text-slate-500">
        {resolvedControls && !resolvedControls.allow_audio_autoplay
          ? "Autoplay is off for this reading profile."
          : isPlaying
            ? "Narration is following the current page."
            : "Press play to hear this page aloud."}
      </p>
    </section>
  );
}
