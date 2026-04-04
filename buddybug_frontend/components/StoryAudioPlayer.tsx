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

const PLAYBACK_START_DELAY_MS = 2000;

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
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
  const loadedSegmentUrlRef = useRef("");
  const latestSegmentIndexRef = useRef(0);
  const latestOrderedSegmentsRef = useRef<NarrationSegmentRead[]>([]);
  const latestEnabledRef = useRef(false);
  const latestStoryReadsItselfRef = useRef(false);
  const latestOnPageChangeRef = useRef(onPageChange);
  const pendingSegmentPageRef = useRef<number | null>(null);
  const playbackRequestIdRef = useRef(0);
  const [enabled, setEnabled] = useState(false);
  const [storyReadsItself, setStoryReadsItself] = useState(false);
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  function cancelPendingPlayback() {
    playbackRequestIdRef.current += 1;
  }

  const orderedSegments = useMemo(() => {
    return [...narration.segments].sort((a, b) => a.page_number - b.page_number);
  }, [narration.segments]);

  const currentSegment: NarrationSegmentRead | null = orderedSegments[segmentIndex] ?? null;
  const currentSegmentUrl = currentSegment ? resolveApiUrl(currentSegment.audio_url) : "";

  useEffect(() => {
    const audio = new Audio();
    audio.preload = "auto";
    audioRef.current = audio;

    return () => {
      cancelPendingPlayback();
      audio.pause();
      audio.src = "";
      audio.onplay = null;
      audio.onpause = null;
      audio.onended = null;
      audioRef.current = null;
    };
  }, []);

  useEffect(() => {
    latestSegmentIndexRef.current = segmentIndex;
    latestOrderedSegmentsRef.current = orderedSegments;
    latestEnabledRef.current = enabled;
    latestStoryReadsItselfRef.current = storyReadsItself;
    latestOnPageChangeRef.current = onPageChange;
  }, [enabled, onPageChange, orderedSegments, segmentIndex, storyReadsItself]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    audio.onplay = () => {
      setIsPlaying(true);
      void trackAudioStarted(bookId, narration.voice.display_name, {
        token,
        user,
        language,
        childProfileId,
      });
    };

    audio.onpause = () => {
      setIsPlaying(false);
    };

    audio.onerror = () => {
      const mediaError = audio.error;
      const detail = mediaError ? `media error ${mediaError.code}` : "unknown media error";
      const message = `Narration could not play (${detail}).`;
      console.error("[StoryAudioPlayer]", message, {
        bookId,
        src: audio.currentSrc,
        pageNumber: latestOrderedSegmentsRef.current[latestSegmentIndexRef.current]?.page_number,
      });
    };

    audio.onended = () => {
      setIsPlaying(false);
      void trackAudioCompleted(bookId, narration.voice.display_name, {
        token,
        user,
        language,
        childProfileId,
      });
      const nextIndex = latestSegmentIndexRef.current + 1;
      const nextSegment = latestOrderedSegmentsRef.current[nextIndex];
      if (
        !latestEnabledRef.current ||
        !nextSegment ||
        !latestStoryReadsItselfRef.current
      ) {
        return;
      }
      void startPlaybackAtIndex(nextIndex, {
        autoAdvance: true,
        syncPage: true,
      });
    };
  }, [bookId, childProfileId, language, narration.voice.display_name, token, user]);

  async function startPlaybackAtIndex(
    targetIndex: number,
    options: { autoAdvance: boolean; syncPage: boolean },
  ) {
    const audio = audioRef.current;
    if (!audio || !orderedSegments.length) {
      return;
    }

    const targetSegment = orderedSegments[targetIndex];
    const targetSegmentUrl = targetSegment ? resolveApiUrl(targetSegment.audio_url) : "";
    if (!targetSegment || !targetSegmentUrl) {
      return;
    }

    playbackRequestIdRef.current += 1;
    const requestId = playbackRequestIdRef.current;

    setEnabled(true);
    setStoryReadsItself(options.autoAdvance);
    setSegmentIndex(targetIndex);
    setIsPlaying(false);

    audio.pause();
    audio.src = targetSegmentUrl;
    audio.currentTime = 0;
    audio.load();
    loadedSegmentUrlRef.current = targetSegmentUrl;

    if (options.syncPage && targetSegment.page_number !== currentPageNumber) {
      pendingSegmentPageRef.current = targetSegment.page_number;
      latestOnPageChangeRef.current(targetSegment.page_number, { behavior: "smooth" });
    }

    await delay(PLAYBACK_START_DELAY_MS);
    if (playbackRequestIdRef.current !== requestId) {
      return;
    }

    try {
      await audio.play();
    } catch (error) {
      const message =
        error instanceof Error
          ? `${error.name}: ${error.message}`
          : "Unable to start narration playback.";
      console.error("[StoryAudioPlayer] play() failed", {
        message,
        bookId,
        src: targetSegmentUrl,
        pageNumber: targetSegment.page_number,
      });
      window.setTimeout(() => {
        if (playbackRequestIdRef.current !== requestId) {
          return;
        }
        void audio.play()
          .then(() => undefined)
          .catch((retryError) => {
            const retryMessage =
              retryError instanceof Error
                ? `${retryError.name}: ${retryError.message}`
                : "Unable to continue narration playback.";
            console.error("[StoryAudioPlayer] retry play() failed", {
              message: retryMessage,
              bookId,
              src: targetSegmentUrl,
              pageNumber: targetSegment.page_number,
            });
          });
      }, 100);
    }
  }

  async function playCurrentSegment(enableAutoAdvance: boolean) {
    let targetIndex = segmentIndex;
    if (currentPageNumber === 0 || orderedSegments[targetIndex]?.page_number === 0) {
      const firstStoryIndex = orderedSegments.findIndex((segment) => segment.page_number > 0);
      if (firstStoryIndex >= 0) {
        targetIndex = firstStoryIndex;
      }
    }

    await startPlaybackAtIndex(targetIndex, {
      autoAdvance: enableAutoAdvance,
      syncPage: true,
    });
  }

  useEffect(() => {
    if (pendingSegmentPageRef.current !== null) {
      if (currentPageNumber !== pendingSegmentPageRef.current) {
        return;
      }
      pendingSegmentPageRef.current = null;
    }

    const matchedIndex = orderedSegments.findIndex((segment) => segment.page_number === currentPageNumber);
    if (matchedIndex >= 0 && matchedIndex !== segmentIndex) {
      setSegmentIndex(matchedIndex);
    }
  }, [currentPageNumber, orderedSegments, segmentIndex]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!currentSegment || !audio) {
      return;
    }
    if (!audio.paused) {
      return;
    }
    if (loadedSegmentUrlRef.current !== currentSegmentUrl) {
      audio.src = currentSegmentUrl;
      audio.load();
      loadedSegmentUrlRef.current = currentSegmentUrl;
    }
  }, [currentSegment, currentSegmentUrl]);

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
    <section className="rounded-[2rem] border border-white/70 bg-white/92 p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => {
            setEnabled((current) => {
              const next = !current;
              if (!next) {
                cancelPendingPlayback();
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
          disabled={!currentSegment}
          onClick={() => {
            if (isPlaying) {
              cancelPendingPlayback();
              setStoryReadsItself(false);
              audioRef.current?.pause();
              return;
            }
            void playCurrentSegment(true);
          }}
          className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${
            enabled || isPlaying
              ? "bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
              : "border border-slate-200 bg-white text-slate-900"
          } disabled:cursor-not-allowed disabled:opacity-50`}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
      </div>
    </section>
  );
}
