/**
 * Sources listing component.
 * @param {{sources: Array<{file: string, page: number}>}} props
 */
export default function SourcesPanel({ sources, onSelectSource }) {
  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
      <div className="flex items-center justify-between">
        <h3 className="text-sm uppercase tracking-[0.2em] text-slate-500">Sources</h3>
        <span className="text-xs text-slate-500">{sources.length} items</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {sources.length === 0 ? (
          <span className="text-sm text-slate-500">No sources available.</span>
        ) : (
          sources.map((source, index) => (
            <button
              type="button"
              key={`${source.file}-${source.page}-${index}`}
              onClick={() => onSelectSource?.(source)}
              className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs text-slate-200 transition hover:border-cyan-500/50"
            >
              {source.file} · {source.page}
              {source.company ? ` · ${source.company}` : ""}
              {typeof source.score === "number" ? ` · ${source.score}` : ""}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
