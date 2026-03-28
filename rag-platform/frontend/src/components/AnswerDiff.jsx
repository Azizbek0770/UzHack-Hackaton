function tokenize(text) {
  return text.trim().split(/\s+/).filter(Boolean);
}

export default function AnswerDiff({ previousAnswer, currentAnswer }) {
  if (!previousAnswer || !currentAnswer || previousAnswer === currentAnswer) {
    return null;
  }

  const prevTokens = tokenize(previousAnswer);
  const currTokens = tokenize(currentAnswer);
  const prevSet = new Set(prevTokens);
  const currSet = new Set(currTokens);
  const added = currTokens.filter((token) => !prevSet.has(token));
  const removed = prevTokens.filter((token) => !currSet.has(token));

  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
      <h3 className="text-sm uppercase tracking-[0.2em] text-slate-500">Answer Diff</h3>
      <div className="mt-4 space-y-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-400">Added</p>
          <p className="mt-2 text-sm text-slate-200">{added.slice(0, 30).join(" ") || "No added tokens"}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-rose-400">Removed</p>
          <p className="mt-2 text-sm text-slate-200">{removed.slice(0, 30).join(" ") || "No removed tokens"}</p>
        </div>
      </div>
    </div>
  );
}
