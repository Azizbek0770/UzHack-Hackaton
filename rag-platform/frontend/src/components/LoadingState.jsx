/**
 * Loading indicator component.
 */
export default function LoadingState() {
  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
      <div className="flex items-center gap-3">
        <span className="spinner" />
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
          Retrieving
        </p>
      </div>
      <div className="mt-4 h-4 w-1/3 animate-pulse rounded bg-slate-700" />
      <div className="mt-4 h-4 w-full animate-pulse rounded bg-slate-800" />
      <div className="mt-2 h-4 w-5/6 animate-pulse rounded bg-slate-800" />
    </div>
  );
}
