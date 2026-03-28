/**
 * Response time display.
 * @param {{value?: number}} props
 */
export default function ResponseTime({ value }) {
  if (!value && value !== 0) {
    return null;
  }
  return (
    <span className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1 text-xs text-slate-400">
      Response {value} ms
    </span>
  );
}
