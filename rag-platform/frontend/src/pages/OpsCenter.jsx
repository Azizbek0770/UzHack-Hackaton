import PipelineDebugPanel from "../components/PipelineDebugPanel.jsx";

export default function OpsCenter() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900">
      <div className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-16">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Operations</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-100">Monitoring & Traceability</h1>
          <p className="mt-2 text-sm text-slate-400">
            Monitor ingestion, retrieval index state, and recent audited query activity.
          </p>
        </div>
        <PipelineDebugPanel />
      </div>
    </div>
  );
}
