export default function SourcePreviewModal({ source, onClose }) {
  if (!source) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4">
      <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-card">
        <div className="flex items-center justify-between">
          <h3 className="text-sm uppercase tracking-[0.2em] text-slate-400">Source Preview</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-700 px-2 py-1 text-xs text-slate-300 transition hover:border-cyan-500/50"
          >
            Close
          </button>
        </div>
        <div className="mt-4 space-y-2 text-sm text-slate-200">
          <p>File: {source.file}</p>
          <p>Page/Sheet: {source.page}</p>
          <p>Company: {source.company || "N/A"}</p>
          <p>Type: {source.doc_type || "N/A"}</p>
          <p>Score: {typeof source.score === "number" ? source.score : "N/A"}</p>
        </div>
      </div>
    </div>
  );
}
