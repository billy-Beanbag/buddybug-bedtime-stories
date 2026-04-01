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
  onPageChange: (pageNumber: number, options?: { behavior?: ScrollBehavior }) => void;
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
  const resumeDelayMs = useRef(0);
  const resumeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [enabled, setEnabled] = useState(true);
  const [storyReadsItself, setStoryReadsItself] = useState(false);
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [progressPercent, setProgressPercent] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const orderedSegments = useMemo(() => {
    return [...narration.segments].sort((a, b) => a.page_number - b.page_number);
  }, [narration.segments]);

  const currentSegment: NarrationSegmentRead | null = orderedSegments[segmentIndex] ?? null;
  const autoplayAllowed = resolvedControls?.allow_audio_autoplay ?? true;

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
    if (resumeTimeoutRef.current) {
      clearTimeout(resumeTimeoutRef.current);
      resumeTimeoutRef.current = null;
    }
    audioRef.current.src = resolveApiUrl(currentSegment.audio_url);
    audioRef.current.load();
    setProgressPercent(0);
    if (enabled && shouldResumeAfterAdvance.current && autoplayAllowed) {
      const delayMs = resumeDelayMs.current;
      if (delayMs > 0) {
        resumeTimeoutRef.current = setTimeout(() => {
          void audioRef.current?.play().catch(() => undefined);
          resumeTimeoutRef.current = null;
        }, delayMs);
      } else {
        void audioRef.current.play().catch(() => undefined);
      }
    }
    shouldResumeAfterAdvance.current = false;
    resumeDelayMs.current = 0;
  }, [autoplayAllowed, currentSegment, enabled]);

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

  useEffect(() => {
    return () => {
      if (resumeTimeoutRef.current) {
        clearTimeout(resumeTimeoutRef.current);
      }
    };
  }, []);

  if (!currentSegment) {
    return null;
  }

  const canAutoAdvance = autoplayAllowed;

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
                setStoryReadsItself(false);
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

      <div className="overflow-hidden rounded-[1.75rem] border border-indigo-100 bg-[linear-gradient(135deg,rgba(224,231,255,0.98),rgba(243,232,255,0.94))] shadow-[0_20px_50px_rgba(79,70,229,0.10)]">
        <div className="space-y-4 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="inline-flex rounded-full border border-indigo-200/80 bg-white/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-700">
                Hands-free bedtime mode
              </div>
              <h4 className="mt-3 text-base font-semibold text-slate-900">Let Buddybug read the story from start to finish</h4>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                The story will drift forward one page at a time, with a gentle pause between pages so the reading feels calm.
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-white/80 bg-white/80 px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm">
              <span className={`h-2.5 w-2.5 rounded-full ${storyReadsItself ? "bg-emerald-500" : "bg-slate-300"}`} />
              {storyReadsItself ? "Active" : "Manual"}
            </div>
          </div>

          <div className="grid gap-2 text-sm text-slate-600 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/70 bg-white/70 px-3 py-3">
              Starts from the current page
            </div>
            <div className="rounded-2xl border border-white/70 bg-white/70 px-3 py-3">
              Smoothly scrolls to each next page
            </div>
            <div className="rounded-2xl border border-white/70 bg-white/70 px-3 py-3">
              Keeps read-along features separate
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-500">
              {canAutoAdvance
                ? "Designed for the bedtime library experience rather than read-along books."
                : "Autoplay is currently disabled by parental controls, so this mode cannot run continuously."}
            </p>
            <button
              type="button"
              disabled={!canAutoAdvance}
              onClick={() => {
                const next = !storyReadsItself;
                setStoryReadsItself(next);
                if (next) {
                  setEnabled(true);
                  resumeDelayMs.current = 0;
                  void audioRef.current?.play().catch(() => undefined);
                }
              }}
              className="rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-5 py-3 text-sm font-semibold text-white shadow-[0_18px_38px_rgba(79,70,229,0.22)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {storyReadsItself ? "Hands-free reading on" : "Start hands-free reading"}
            </button>
          </div>
        </div>
      </div>

      <audio
        ref={audioRef}
        controls
        autoPlay={Boolean(autoplayAllowed && enabled)}
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
          if (!enabled || !nextSegment || !storyReadsItself) {
            return;
          }
          shouldResumeAfterAdvance.current = Boolean(autoplayAllowed);
          resumeDelayMs.current = 550;
          setSegmentIndex(nextIndex);
          onPageChange(nextSegment.page_number, { behavior: "smooth" });
        }}
      >
        Your browser does not support audio playback.
      </audio>

      <p className="text-xs text-slate-500">
        {resolvedControls && !resolvedControls.allow_audio_autoplay
          ? "Autoplay is off for this reading profile, so story-reads-itself mode is unavailable."
          : storyReadsItself
            ? "Buddybug is moving through the story for you one page at a time."
          : isPlaying
            ? "Narration is following the current page."
            : "Press play to hear this page aloud."}
      </p>
    </section>
  );
}
