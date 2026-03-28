import { useEffect, useState } from "react";
import { getAuditRuns, getHealth, getIngestionReport, getMetrics } from "../services/api.js";

export default function PipelineDebugPanel() {
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [report, setReport] = useState(null);
  const [audit, setAudit] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      const [nextHealth, nextMetrics, nextReport, nextAudit] = await Promise.all([
        getHealth(),
        getMetrics(),
        getIngestionReport(),
        getAuditRuns()
      ]);
      setHealth(nextHealth);
      setMetrics(nextMetrics);
      setReport(nextReport);
      setAudit(nextAudit);
    } catch (err) {
      setError(err.message || "Failed to load debug data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
      <div className="flex items-center justify-between">
        <h3 className="text-sm uppercase tracking-[0.2em] text-slate-500">Pipeline Debug</h3>
        <button
          type="button"
          onClick={refresh}
          disabled={loading}
          className="rounded-lg border border-slate-700 px-2 py-1 text-xs text-slate-300 transition hover:border-cyan-500/50 disabled:opacity-50"
        >
          {loading ? "Refreshing" : "Refresh"}
        </button>
      </div>
      {error ? (
        <p className="mt-3 text-xs text-rose-300">{error}</p>
      ) : (
        <div className="mt-4 space-y-2 text-xs text-slate-300">
          <p>Status: {health?.status || "unknown"}</p>
          <p>Text index: {health?.retrieval?.text_chunks ?? "-"}</p>
          <p>Table index: {health?.retrieval?.table_chunks ?? "-"}</p>
          <p>Ingest processed: {report?.processed_files ?? "-"}</p>
          <p>Ingest failed: {report?.failed_files ?? "-"}</p>
          <p>
            Last failed file: {report?.files?.find((item) => item.error)?.file_path || "none"}
          </p>
          <p>Audit ingestion runs: {audit?.ingestion_runs?.length ?? "-"}</p>
          <p>Audit QA runs: {audit?.qa_runs?.length ?? "-"}</p>
          <p>Last audited query: {audit?.qa_runs?.[0]?.question ?? "none"}</p>
          <p>Latency avg: {metrics?.latency_avg_ms ?? "-"}</p>
          <p>Latency p95: {metrics?.latency_p95_ms ?? "-"}</p>
          <p>Confidence avg: {metrics?.confidence_avg ?? "-"}</p>
        </div>
      )}
    </div>
  );
}
