export default function QueryHistory({ items, onSelect }) {
  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
      <div className="flex items-center justify-between">
        <h3 className="text-sm uppercase tracking-[0.2em] text-slate-500">Query History</h3>
        <span className="text-xs text-slate-500">{items.length} items</span>
      </div>
      <div className="mt-4 space-y-2">
        {items.length === 0 ? (
          <p className="text-sm text-slate-500">No previous queries.</p>
        ) : (
          items.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelect(item)}
              type="button"
              className="w-full rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2 text-left transition hover:border-cyan-500/50"
            >
              <p className="truncate text-sm text-slate-200">{item.question}</p>
              <p className="mt-1 truncate text-xs text-slate-500">{item.answer}</p>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
