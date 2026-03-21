interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div className="rounded-3xl border border-white/60 bg-white/80 p-6 text-center text-sm text-slate-600 shadow-sm">
      {message}
    </div>
  );
}
