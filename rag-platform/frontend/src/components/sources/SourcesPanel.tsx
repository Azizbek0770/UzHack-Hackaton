import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Table2, ChevronDown } from 'lucide-react'
import clsx from 'clsx'
import type { SourceReference } from '../../services/types'

interface SourcesPanelProps {
  sources: SourceReference[]
}

const DOC_TYPE_LABELS: Record<string, string> = {
  financial_report: 'Moliyaviy hisobot',
  annual_report: 'Yillik hisobot',
  disclosure: 'Ma\'lumot oshkoraligi',
  metadata: 'Metama\'lumotlar',
  unknown: 'Hujjat',
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  if (!sources.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-3xl mx-auto"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 px-1">
        <div className="h-px flex-1 bg-obsidian-700" />
        <span className="text-xs text-obsidian-500 font-medium uppercase tracking-widest">
          Manbalar ({sources.length})
        </span>
        <div className="h-px flex-1 bg-obsidian-700" />
      </div>

      {/* Source cards */}
      <div className="flex flex-wrap gap-2">
        {sources.map((src, i) => (
          <SourceTag key={i} source={src} index={i} />
        ))}
      </div>
    </motion.div>
  )
}

// ── Individual source tag with expand ────────────────────────────────────────

function SourceTag({ source, index }: { source: SourceReference; index: number }) {
  const [expanded, setExpanded] = useState(false)
  const hasExcerpt = !!source.excerpt
  const isTable = source.chunk_type === 'table'
  const Icon = isTable ? Table2 : FileText

  const location = source.page
    ? `bet ${source.page}`
    : source.sheet
    ? `Varaq: ${source.sheet}`
    : null

  const docLabel = DOC_TYPE_LABELS[source.doc_type] ?? 'Hujjat'

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.06, duration: 0.3 }}
      className="flex flex-col"
    >
      <button
        onClick={() => hasExcerpt && setExpanded((v) => !v)}
        className={clsx(
          'flex items-center gap-2 px-3 py-2 rounded-xl border transition-all duration-200 text-left',
          'bg-obsidian-800 border-obsidian-700',
          hasExcerpt
            ? 'hover:border-gold-500/25 hover:bg-obsidian-700 cursor-pointer'
            : 'cursor-default',
          expanded && 'border-gold-500/25 rounded-b-none border-b-0'
        )}
      >
        {/* Icon */}
        <span className={clsx(
          'shrink-0 p-1 rounded-md',
          isTable ? 'bg-jade-500/10 text-jade-400' : 'bg-gold-500/10 text-gold-400'
        )}>
          <Icon size={12} />
        </span>

        {/* File info */}
        <div className="flex flex-col min-w-0">
          <span className="text-xs text-gray-300 font-medium truncate max-w-[200px]">
            {source.file}
          </span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[10px] text-obsidian-500">
              {source.company}
            </span>
            {location && (
              <>
                <span className="text-obsidian-700">·</span>
                <span className="text-[10px] font-mono text-obsidian-500">
                  {location}
                </span>
              </>
            )}
            <span className="text-obsidian-700">·</span>
            <span className={clsx(
              'text-[10px] px-1 py-0.5 rounded',
              isTable
                ? 'text-jade-500 bg-jade-500/10'
                : 'text-gold-500 bg-gold-500/10'
            )}>
              {docLabel}
            </span>
          </div>
        </div>

        {/* Expand chevron */}
        {hasExcerpt && (
          <ChevronDown
            size={12}
            className={clsx(
              'ml-auto shrink-0 text-obsidian-600 transition-transform duration-200',
              expanded && 'rotate-180'
            )}
          />
        )}
      </button>

      {/* Expanded excerpt */}
      <AnimatePresence>
        {expanded && source.excerpt && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
            className="overflow-hidden"
          >
            <div className={clsx(
              'px-4 py-3 rounded-b-xl border border-t-0',
              'bg-obsidian-800/50 border-gold-500/20',
              'text-xs text-obsidian-400 leading-relaxed font-mono',
            )}>
              <div className="text-[10px] text-gold-500/60 mb-1 uppercase tracking-wider">
                Hujjat parchasi
              </div>
              {source.excerpt}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
