/**
 * Answer display card.
 * @param {{answer: string}} props
 */
export default function AnswerCard({ answer, hint }) {
  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-card animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-sm uppercase tracking-[0.2em] text-slate-500">Answer</h2>
        <span className="rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1 text-xs text-slate-400">
          Grounded
        </span>
      </div>
      <p className="mt-4 whitespace-pre-line text-lg text-slate-100">{answer}</p>
      {hint ? <p className="mt-3 text-sm text-amber-300">{hint}</p> : null}
    </div>
  );
}
