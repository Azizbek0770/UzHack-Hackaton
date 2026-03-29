import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bug, ChevronDown, Timer, FileSearch, Table2, AlignLeft } from 'lucide-react'
import clsx from 'clsx'
import type { DebugInfo } from '../../services/types'

interface DebugPanelProps {
  debug: DebugInfo
}

export function DebugPanel({ debug }: DebugPanelProps) {
  const [open, setOpen] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.4 }}
      className="w-full max-w-3xl mx-auto"
    >
      {/* Toggle button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          'w-full flex items-center justify-between px-4 py-3 rounded-xl border transition-all',
          open
            ? 'bg-gold-500/5 border-gold-500/20 rounded-b-none'
            : 'bg-obsidian-900 border-obsidian-700 hover:border-gold-500/20'
        )}
      >
        <div className="flex items-center gap-2">
          <Bug size={13} className="text-gold-500" />
          <span className="text-xs font-semibold text-gold-400 uppercase tracking-wider">
            Debug Info
          </span>
          <span className="text-xs text-obsidian-500">
            {debug.retrieved_text_chunks} текст · {debug.retrieved_table_chunks} таблиц
          </span>
        </div>
        <ChevronDown
          size={14}
          className={clsx(
            'text-obsidian-500 transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="overflow-hidden"
          >
            <div className="bg-obsidian-900 border border-t-0 border-gold-500/20 rounded-b-xl p-4 space-y-5">

              {/* Stage timings */}
              {Object.keys(debug.stage_timings).length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Timer size={12} className="text-gold-400" />
                    <span className="text-xs font-semibold text-gold-400 uppercase tracking-wider">
                      Pipeline Timings
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(debug.stage_timings).map(([stage, ms]) => (
                      <div
                        key={stage}
                        className="flex items-center justify-between px-3 py-2 rounded-lg bg-obsidian-800"
                      >
                        <span className="text-xs text-obsidian-400 font-mono">{stage}</span>
                        <span className="text-xs font-mono text-gold-400">
                          {ms.toFixed(1)}ms
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Top retrieved chunks */}
              {debug.top_chunks.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <FileSearch size={12} className="text-jade-400" />
                    <span className="text-xs font-semibold text-jade-400 uppercase tracking-wider">
                      Top Retrieved Chunks
                    </span>
                  </div>
                  <div className="space-y-2">
                    {debug.top_chunks.map((chunk, i) => {
                      const isTable = chunk.type === 'table'
                      return (
                        <div
                          key={i}
                          className="rounded-lg border border-obsidian-700 bg-obsidian-800 overflow-hidden"
                        >
                          <div className="flex items-center justify-between px-3 py-2 border-b border-obsidian-700">
                            <div className="flex items-center gap-2">
                              <span className={clsx(
                                'text-[10px] p-1 rounded',
                                isTable
                                  ? 'text-jade-400 bg-jade-500/10'
                                  : 'text-gold-400 bg-gold-500/10'
                              )}>
                                {isTable ? <Table2 size={10} /> : <AlignLeft size={10} />}
                              </span>
                              <span className="text-xs text-gray-400 font-medium truncate max-w-[200px]">
                                {chunk.source}
                              </span>
                            </div>
                            <span className="font-mono text-xs text-jade-400">
                              {chunk.score.toFixed(4)}
                            </span>
                          </div>
                          <p className="px-3 py-2 text-[11px] font-mono text-obsidian-400 leading-relaxed line-clamp-3">
                            {chunk.excerpt}
                          </p>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Rewritten query */}
              {debug.rewritten_query && debug.rewritten_query !== '' && (
                <div>
                  <span className="text-xs text-obsidian-500 uppercase tracking-wider">
                    Rewritten Query:
                  </span>
                  <p className="mt-1 text-xs font-mono text-gold-300 bg-obsidian-800 px-3 py-2 rounded-lg">
                    {debug.rewritten_query}
                  </p>
                </div>
              )}

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
