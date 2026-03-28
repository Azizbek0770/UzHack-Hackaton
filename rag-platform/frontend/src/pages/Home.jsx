import { useRef, useState } from "react";
import AnswerDiff from "../components/AnswerDiff.jsx";
import AnswerCard from "../components/AnswerCard.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import LoadingState from "../components/LoadingState.jsx";
import PipelineDebugPanel from "../components/PipelineDebugPanel.jsx";
import QueryHistory from "../components/QueryHistory.jsx";
import ResponseTime from "../components/ResponseTime.jsx";
import SearchBar from "../components/SearchBar.jsx";
import SourcePreviewModal from "../components/SourcePreviewModal.jsx";
import SourcesPanel from "../components/SourcesPanel.jsx";
import { queryRag } from "../services/api.js";

/**
 * Main dashboard page.
 */
export default function Home() {
  const requestControllerRef = useRef(null);
  const userCanceledRef = useRef(false);
  const [question, setQuestion] = useState("");
  const [company, setCompany] = useState("");
  const [docType, setDocType] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [responseTime, setResponseTime] = useState(null);
  const [queryMode, setQueryMode] = useState(null);
  const [answerConfidence, setAnswerConfidence] = useState(null);
  const [contradictionWarning, setContradictionWarning] = useState(false);
  const [history, setHistory] = useState([]);
  const [previousAnswer, setPreviousAnswer] = useState("");
  const [selectedSource, setSelectedSource] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const hasAnswer = Boolean(answer);
  const sourceCount = sources.length;
  const answerHint =
    !loading &&
    answer === "Insufficient context to answer from provided documents." &&
    sources.length === 0 &&
    queryMode === "table"
      ? "No table evidence found for current filters. Upload XLSX financial reports in Data Hub or switch Document Type to All/Text."
      : "";
  const suggestions = [
    "Выручка компании за 2023 год",
    "Активы и обязательства за 2022",
    "What is the EBITDA trend?",
    "Daromad 2021 yil uchun qancha?"
  ];

  const handleSubmit = async (overrideQuestion) => {
    const resolvedQuestion =
      typeof overrideQuestion === "string" ? overrideQuestion : question;
    const nextQuestion = resolvedQuestion.trim();
    if (!nextQuestion || loading) {
      return;
    }
    if (requestControllerRef.current) {
      requestControllerRef.current.abort();
    }
    userCanceledRef.current = false;
    requestControllerRef.current = new AbortController();
    setLoading(true);
    setError("");
    const start = performance.now();
    try {
      if (typeof overrideQuestion === "string" && overrideQuestion.trim()) {
        setQuestion(overrideQuestion);
      }
      const data = await queryRag(nextQuestion, {
        company: company.trim() || undefined,
        doc_type: docType || undefined,
        signal: requestControllerRef.current.signal,
        timeoutMs: 45000
      });
      setPreviousAnswer(answer);
      setAnswer(data.answer);
      setSources(data.relevant_chunks || []);
      setQueryMode(data.query_mode || null);
      setAnswerConfidence(
        typeof data.answer_confidence === "number" ? data.answer_confidence : null
      );
      setContradictionWarning(Boolean(data.contradiction_warning));
      setResponseTime(
        data.response_time_ms ?? Math.round(performance.now() - start)
      );
      setHistory((prev) => [
        {
          id: `${Date.now()}-${Math.random()}`,
          question: nextQuestion,
          answer: data.answer,
          sources: data.relevant_chunks || [],
          query_mode: data.query_mode || null
        },
        ...prev
      ].slice(0, 12));
    } catch (err) {
      if (err.name === "AbortError") {
        setError(
          userCanceledRef.current
            ? "Search cancelled."
            : "Search timed out. Please refine your question or filters."
        );
        setResponseTime(null);
        return;
      }
      setError(err.message || "Unexpected error");
      setAnswer("");
      setSources([]);
      setQueryMode(null);
      setAnswerConfidence(null);
      setContradictionWarning(false);
      setResponseTime(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    userCanceledRef.current = true;
    if (requestControllerRef.current) {
      requestControllerRef.current.abort();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col items-center px-6 py-16">
        <div className="grid w-full gap-6 lg:grid-cols-[1fr_320px]">
          <div className="flex w-full flex-col items-center gap-10">
          <div className="flex w-full flex-col items-center gap-6 text-center">
            <div className="flex items-center gap-3 rounded-full border border-slate-800 bg-slate-900/60 px-4 py-2 text-xs text-slate-400">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              Production RAG Platform
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-slate-500">
                Financial RAG Assistant
              </p>
              <h1 className="mt-3 text-4xl font-semibold text-slate-100">
                Ask your documents about any company
              </h1>
              <p className="mt-3 text-sm text-slate-400">
                Grounded answers with transparent sources across PDF, XLSX, and JSON.
              </p>
            </div>
          </div>
          <SearchBar
            value={question}
            onChange={setQuestion}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            loading={loading}
          />
          <div className="grid w-full max-w-3xl gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 px-4 py-3">
              <label className="text-xs uppercase tracking-[0.2em] text-slate-500">
                Company Filter
              </label>
              <input
                className="mt-2 w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none"
                placeholder="Optional company name"
                value={company}
                onChange={(event) => setCompany(event.target.value)}
              />
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 px-4 py-3">
              <label className="text-xs uppercase tracking-[0.2em] text-slate-500">
                Document Type
              </label>
              <select
                className="mt-2 w-full bg-transparent text-sm text-slate-100 focus:outline-none"
                value={docType}
                onChange={(event) => setDocType(event.target.value)}
              >
                <option value="">All</option>
                <option value="pdf">PDF</option>
                <option value="xlsx">XLSX</option>
                <option value="json">JSON</option>
              </select>
            </div>
          </div>
          <div className="flex w-full max-w-3xl flex-wrap gap-2">
            {suggestions.map((item) => (
              <button
                key={item}
                className="rounded-full border border-slate-800 bg-slate-900/40 px-4 py-2 text-xs text-slate-300 transition hover:border-cyan-500/60 hover:text-slate-100"
                onClick={() => handleSubmit(item)}
                type="button"
              >
                {item}
              </button>
            ))}
          </div>
          {error && <ErrorBanner message={error} />}
          {loading && <LoadingState />}
          {!loading && !hasAnswer && !error && (
            <div className="w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-center text-sm text-slate-500">
              Ask a question to see an answer with cited sources.
            </div>
          )}
          {!loading && hasAnswer && (
            <div className="flex w-full flex-col gap-6">
              <div className="flex flex-wrap items-center gap-3">
                <ResponseTime value={responseTime} />
                <span className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1 text-xs text-slate-400">
                  Sources {sourceCount}
                </span>
                {company && (
                  <span className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1 text-xs text-slate-400">
                    {company}
                  </span>
                )}
                {docType && (
                  <span className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-1 text-xs text-slate-400">
                    {docType.toUpperCase()}
                  </span>
                )}
                {queryMode && (
                  <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-300">
                    Mode {queryMode.toUpperCase()}
                  </span>
                )}
                {typeof answerConfidence === "number" && (
                  <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                    Confidence {Math.round(answerConfidence * 100)}%
                  </span>
                )}
                {contradictionWarning && (
                  <span className="rounded-full border border-rose-500/40 bg-rose-500/10 px-3 py-1 text-xs text-rose-300">
                    Check numeric consistency
                  </span>
                )}
              </div>
              <AnswerCard answer={answer} hint={answerHint} />
              <AnswerDiff previousAnswer={previousAnswer} currentAnswer={answer} />
              <SourcesPanel sources={sources} onSelectSource={setSelectedSource} />
            </div>
          )}
          </div>
          <div className="w-full lg:pt-20">
            <div className="space-y-4">
              <PipelineDebugPanel />
            <QueryHistory
              items={history}
              onSelect={(item) => {
                setQuestion(item.question);
                setAnswer(item.answer);
                setSources(item.sources || []);
                setQueryMode(item.query_mode || null);
              }}
            />
            </div>
          </div>
        </div>
      </div>
      <SourcePreviewModal source={selectedSource} onClose={() => setSelectedSource(null)} />
    </div>
  );
}
