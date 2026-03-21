interface ReaderControlsProps {
  currentPageNumber: number;
  totalPageNumber: number;
  canGoPrevious: boolean;
  canGoNext: boolean;
  isLastPage: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onMarkFinished?: () => void;
}

export function ReaderControls({
  currentPageNumber,
  totalPageNumber,
  canGoPrevious,
  canGoNext,
  isLastPage,
  onPrevious,
  onNext,
  onMarkFinished,
}: ReaderControlsProps) {
  return (
    <div className="space-y-3 rounded-[2rem] border border-white/70 bg-white/92 p-4 shadow-sm">
      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>Reading controls</span>
        <span>
          {currentPageNumber} / {totalPageNumber}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={onPrevious}
          disabled={!canGoPrevious}
          className="min-h-12 rounded-2xl border border-slate-200 bg-white px-4 py-3 font-medium text-slate-900 disabled:opacity-50"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!canGoNext}
          className="min-h-12 rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-50"
        >
          {isLastPage ? "At final page" : "Next"}
        </button>
      </div>

      {isLastPage && onMarkFinished ? (
        <button
          type="button"
          onClick={onMarkFinished}
          className="min-h-12 w-full rounded-2xl bg-indigo-50 px-4 py-3 font-medium text-indigo-800"
        >
          Mark finished
        </button>
      ) : null}
    </div>
  );
}
