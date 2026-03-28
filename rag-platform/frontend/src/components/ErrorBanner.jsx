/**
 * Error display component.
 * @param {{message: string}} props
 */
export default function ErrorBanner({ message }) {
  return (
    <div className="w-full rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
      <div className="flex items-center justify-between">
        <span>Unable to complete the request</span>
        <span className="text-xs text-red-300/80">Retry</span>
      </div>
      <p className="mt-2 text-xs text-red-300/80">{message}</p>
    </div>
  );
}
