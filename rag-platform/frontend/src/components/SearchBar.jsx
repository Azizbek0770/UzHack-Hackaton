/**
 * Search input component.
 * @param {{value: string, onChange: (value: string) => void, onSubmit: () => void, loading: boolean}} props
 */
export default function SearchBar({ value, onChange, onSubmit, onCancel, loading }) {
  return (
    <div className="w-full max-w-3xl">
      <div className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-card md:flex-row md:items-center">
        <input
          className="flex-1 bg-transparent text-lg text-slate-100 placeholder:text-slate-500 focus:outline-none"
          type="text"
          placeholder="Ask about company financials..."
          aria-label="Question"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              onSubmit();
            }
          }}
        />
        <div className="flex items-center gap-2">
          {loading && (
            <button
              className="rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-300 transition hover:border-rose-500/60"
              onClick={onCancel}
              type="button"
            >
              Cancel
            </button>
          )}
          <button
            className="rounded-xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
            onClick={() => onSubmit()}
            disabled={loading}
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </div>
    </div>
  );
}
