import { useState, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { PanelLeft } from 'lucide-react'
import clsx from 'clsx'

import { QueryInput } from '../components/query/QueryInput'
import { AnswerCard } from '../components/answer/AnswerCard'
import { SourcesPanel } from '../components/sources/SourcesPanel'
import { LoadingSkeleton, ErrorState, EmptyState } from '../components/ui/States'
import { DebugPanel } from '../components/ui/DebugPanel'
import { QueryHistory } from '../components/ui/QueryHistory'
import { StatusBar } from '../components/ui/StatusBar'

import { useQuery, useQueryHistory } from '../hooks/useQuery'
import type { QueryRequest, HistoryEntry } from '../services/types'

export function MainPage() {
  const { response, isLoading, error, submit } = useQuery()
  const { history, addEntry, clearHistory, removeEntry } = useQueryHistory()
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleSubmit = useCallback(
    async (request: QueryRequest) => {
      setCurrentQuestion(request.question)
      const res = await submit(request)
      if (res) {
        addEntry(request.question, res)
      }
    },
    [submit, addEntry]
  )

  const handleHistorySelect = useCallback(
    (entry: HistoryEntry) => {
      setCurrentQuestion(entry.question)
      // Replay the cached response by re-submitting
      handleSubmit({ question: entry.question, debug: false })
      setSidebarOpen(false)
    },
    [handleSubmit]
  )

  return (
    <div className="min-h-screen bg-obsidian-950 grid-bg flex flex-col">

      {/* ── Top Navigation ──────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 glass border-b border-obsidian-700">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">

          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-gold-500 to-gold-300 flex items-center justify-center">
              <span className="text-obsidian-950 font-display text-sm">F</span>
            </div>
            <div>
              <span className="font-display text-lg tracking-wider text-gray-100">
                FINRAG
              </span>
              <span className="ml-2 text-xs text-obsidian-500 font-medium">
                Financial Intelligence
              </span>
            </div>
          </div>

          {/* Status + History toggle */}
          <div className="flex items-center gap-4">
            <StatusBar />
            {history.length > 0 && (
              <button
                onClick={() => setSidebarOpen((v) => !v)}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs transition-all',
                  sidebarOpen
                    ? 'bg-gold-500/10 border-gold-500/25 text-gold-400'
                    : 'bg-obsidian-800 border-obsidian-700 text-obsidian-400 hover:border-obsidian-600'
                )}
              >
                <PanelLeft size={13} />
                История ({history.length})
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ── Main Layout ─────────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* History Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="shrink-0 border-r border-obsidian-700 bg-obsidian-900 overflow-hidden"
            >
              <QueryHistory
                history={history}
                onSelect={handleHistorySelect}
                onClear={clearHistory}
                onRemove={removeEntry}
              />
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Center Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-12 space-y-8">

            {/* ── Hero Header ────────────────────────────────────────── */}
            <AnimatePresence>
              {!response && !isLoading && !error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.5 }}
                  className="text-center space-y-3 pb-4"
                >
                  <h1 className="font-display text-5xl text-gray-100 tracking-widest">
                    FINANCIAL{' '}
                    <span className="gold-gradient">INTELLIGENCE</span>
                  </h1>
                  <p className="text-sm text-obsidian-400 max-w-md mx-auto leading-relaxed">
                    Задайте вопрос о финансовой отчётности компании.
                    Система анализирует PDF, XLSX и корпоративные раскрытия
                    на русском и узбекском языках.
                  </p>

                  {/* Language badges */}
                  <div className="flex items-center justify-center gap-2 pt-1">
                    {['РУС', 'UZB', 'PDF', 'XLSX'].map((tag) => (
                      <span
                        key={tag}
                        className="text-[10px] font-mono px-2 py-0.5 rounded border border-obsidian-700 text-obsidian-500"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Query Input ─────────────────────────────────────────── */}
            <QueryInput
              onSubmit={handleSubmit}
              isLoading={isLoading}
            />

            {/* ── Results Area ─────────────────────────────────────────── */}
            <div className="space-y-4">
              <AnimatePresence mode="wait">
                {/* Loading */}
                {isLoading && (
                  <motion.div key="loading" exit={{ opacity: 0 }}>
                    <LoadingSkeleton />
                  </motion.div>
                )}

                {/* Error */}
                {!isLoading && error && (
                  <motion.div key="error">
                    <ErrorState
                      message={error}
                      onRetry={() =>
                        currentQuestion &&
                        handleSubmit({ question: currentQuestion })
                      }
                    />
                  </motion.div>
                )}

                {/* Results */}
                {!isLoading && !error && response && (
                  <motion.div key="result" className="space-y-4">
                    <AnswerCard response={response} question={currentQuestion} />
                    <SourcesPanel sources={response.relevant_chunks} />
                    {response.debug && (
                      <DebugPanel debug={response.debug} />
                    )}
                  </motion.div>
                )}

                {/* Empty */}
                {!isLoading && !error && !response && (
                  <motion.div key="empty">
                    <EmptyState />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

          </div>
        </main>
      </div>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-obsidian-800 py-3 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span className="text-xs text-obsidian-700">
            FinRAG · RAG Platform v1.0 · Hackathon Edition
          </span>
          <span className="text-xs text-obsidian-700 font-mono">
            bge-m3 · FAISS · BM25
          </span>
        </div>
      </footer>

    </div>
  )
}
