"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { trackAudioCompleted, trackAudioStarted, trackAutoplayBlockedByParentalControls } from "@/lib/analytics";
import { resolveApiUrl } from "@/lib/api";
import type {
  NarrationSegmentRead,
  ReaderNarrationResponse,
  ResolvedParentalControlsResponse,
  User,
} from "@/lib/types";

interface StoryAudioPlayerProps {
  bookId: number;
  narration: ReaderNarrationResponse;
  currentPageNumber: number;
  onPageChange: (pageNumber: number, options?: { behavior?: ScrollBehavior }) => void;
  token?: string | null;
  user?: User | null;
  language?: string;
  childProfileId?: number | null;
  resolvedControls?: ResolvedParentalControlsResponse | null;
}

export function StoryAudioPlayer({
  bookId,
  narration,
  currentPageNumber,
  onPageChange,
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

  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/92 p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => {
            setEnabled((current) => {
              const next = !current;
              if (!next) {
                setStoryReadsItself(false);
                setIsPlaying(false);
                audioRef.current?.pause();
              }
              return next;
            });
          }}
          className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${
            enabled
              ? "bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
              : "border border-slate-200 bg-white text-slate-900"
          }`}
        >
          {enabled ? "Narration on" : "Narration off"}
        </button>
        <button
          type="button"
          disabled={!enabled}
          onClick={() => {
            if (!enabled) {
              return;
            }
            if (isPlaying) {
              setStoryReadsItself(false);
              audioRef.current?.pause();
              return;
            }
            setStoryReadsItself(autoplayAllowed);
            resumeDelayMs.current = 0;
            void audioRef.current?.play().catch(() => undefined);
          }}
          className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${
            enabled
              ? "bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
              : "border border-slate-200 bg-white text-slate-900"
          } disabled:cursor-not-allowed disabled:opacity-50`}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
      </div>

      <audio
        ref={audioRef}
        controls={false}
        autoPlay={false}
        preload="metadata"
        className="hidden"
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
        onEnded={() => {
          setIsPlaying(false);
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
    </section>
  );
}
