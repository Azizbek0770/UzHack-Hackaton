import { useEffect, useMemo, useState } from "react";
import { getUploadedFiles, uploadDocuments } from "../services/api.js";

export default function DataHub() {
  const [company, setCompany] = useState("");
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadedBatches, setUploadedBatches] = useState([]);
  const [error, setError] = useState("");
  const canUpload = company.trim().length > 0 && files.length > 0 && !uploading;

  const totalSizeMb = useMemo(
    () => (files.reduce((sum, file) => sum + file.size, 0) / (1024 * 1024)).toFixed(2),
    [files]
  );

  const refreshUploads = async () => {
    try {
      const data = await getUploadedFiles();
      setUploadedBatches(data.batches || []);
    } catch (err) {
      setError(err.message || "Failed to load uploaded batches");
    }
  };

  useEffect(() => {
    refreshUploads();
  }, []);

  const handleUpload = async () => {
    if (!canUpload) {
      return;
    }
    setUploading(true);
    setError("");
    try {
      const result = await uploadDocuments({
        company: company.trim(),
        files
      });
      setUploadResult(result);
      setFiles([]);
      await refreshUploads();
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-16">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Data Hub</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-100">
            Upload and ingest financial files
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Upload PDF/XLSX/JSON files per company and ingest directly into retrieval indexes.
          </p>
        </div>
        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
            <label className="text-xs uppercase tracking-[0.2em] text-slate-500">Company</label>
            <input
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-slate-100 focus:border-cyan-500/60 focus:outline-none"
              value={company}
              onChange={(event) => setCompany(event.target.value)}
              placeholder="Example: AlphaBank"
            />
            <label className="mt-4 block text-xs uppercase tracking-[0.2em] text-slate-500">Files</label>
            <input
              className="mt-2 block w-full text-sm text-slate-200"
              type="file"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files || []))}
            />
            <p className="mt-2 text-xs text-slate-500">
              Selected {files.length} files · {totalSizeMb} MB
            </p>
            {files.length > 0 && (
              <div className="mt-3 max-h-40 space-y-1 overflow-auto rounded-xl border border-slate-800 bg-slate-950/50 p-3 text-xs text-slate-300">
                {files.map((file) => (
                  <p key={`${file.name}-${file.size}`}>{file.name}</p>
                ))}
              </div>
            )}
            <div className="mt-4 flex items-center gap-2">
              <button
                className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
                type="button"
                onClick={handleUpload}
                disabled={!canUpload}
              >
                {uploading ? "Uploading..." : "Upload & Ingest"}
              </button>
              <button
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 transition hover:border-cyan-500/60"
                type="button"
                onClick={refreshUploads}
              >
                Refresh
              </button>
            </div>
            {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
          </div>
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Latest Ingestion</p>
              {!uploadResult ? (
                <p className="mt-2 text-sm text-slate-500">No upload has been executed in this session.</p>
              ) : (
                <div className="mt-3 space-y-1 text-sm text-slate-200">
                  <p>Processed files: {uploadResult.processed_files}</p>
                  <p>Failed files: {uploadResult.failed_files}</p>
                  <p>Text chunks: {uploadResult.text_chunks}</p>
                  <p>Table chunks: {uploadResult.table_chunks}</p>
                  <p>Batch ID: {uploadResult.batch_id}</p>
                </div>
              )}
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-card">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Uploaded Batches</p>
              {uploadedBatches.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">No batches found.</p>
              ) : (
                <div className="mt-3 max-h-80 space-y-3 overflow-auto text-xs text-slate-300">
                  {uploadedBatches.map((batch) => (
                    <div key={batch.batch_id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                      <p className="font-semibold text-slate-200">{batch.batch_id}</p>
                      <p className="mt-1 text-slate-500">Files: {batch.file_count}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
