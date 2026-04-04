interface ReaderProgressBarProps {
  currentPageNumber: number;
  totalPageNumber: number;
}

export function ReaderProgressBar({
  currentPageNumber,
  totalPageNumber,
}: ReaderProgressBarProps) {
  const safeTotal = Math.max(totalPageNumber, 1);
  const progress = Math.min((currentPageNumber / safeTotal) * 100, 100);

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs font-medium text-slate-500 sm:text-sm">
        <span>
          Page {currentPageNumber} of {totalPageNumber}
        </span>
        <span>{Math.round(progress)}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
