import { motion, AnimatePresence } from 'framer-motion'
import { History, Trash2, Clock, ChevronRight, X } from 'lucide-react'
import clsx from 'clsx'
import type { HistoryEntry } from '../../services/types'

interface QueryHistoryProps {
  history: HistoryEntry[]
  onSelect: (entry: HistoryEntry) => void
  onClear: () => void
  onRemove: (id: string) => void
}

export function QueryHistory({
  history,
  onSelect,
  onClear,
  onRemove,
}: QueryHistoryProps) {
  if (history.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-obsidian-700">
        <div className="flex items-center gap-2">
          <History size={14} className="text-gold-500" />
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            История
          </span>
        </div>
        <button
          onClick={onClear}
          className="p-1 rounded text-obsidian-500 hover:text-crimson-400 transition-colors"
          title="Очистить историю"
        >
          <Trash2 size={13} />
        </button>
      </div>

      {/* Entries */}
      <div className="flex-1 overflow-y-auto py-2">
        <AnimatePresence initial={false}>
          {history.map((entry) => (
            <HistoryItem
              key={entry.id}
              entry={entry}
              onSelect={onSelect}
              onRemove={onRemove}
            />
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

// ── Single history item ───────────────────────────────────────────────────────

function HistoryItem({
  entry,
  onSelect,
  onRemove,
}: {
  entry: HistoryEntry
  onSelect: (e: HistoryEntry) => void
  onRemove: (id: string) => void
}) {
  const confColor =
    entry.response.confidence_level === 'high'
      ? 'text-jade-500'
      : entry.response.confidence_level === 'medium'
      ? 'text-gold-500'
      : 'text-crimson-400'

  const timeStr = new Date(entry.timestamp).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10, height: 0 }}
      transition={{ duration: 0.2 }}
      className="group relative"
    >
      <button
        onClick={() => onSelect(entry)}
        className={clsx(
          'w-full text-left px-4 py-3 transition-colors duration-150',
          'hover:bg-obsidian-800 border-b border-obsidian-800',
          'focus-visible:bg-obsidian-800'
        )}
      >
        <div className="flex items-start gap-2 pr-6">
          <ChevronRight
            size={12}
            className="mt-0.5 shrink-0 text-obsidian-600 group-hover:text-gold-500 transition-colors"
          />
          <div className="min-w-0 flex-1">
            <p className="text-xs text-gray-300 leading-snug line-clamp-2">
              {entry.question}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <Clock size={9} className="text-obsidian-600" />
              <span className="text-[10px] text-obsidian-600">{timeStr}</span>
              <span className={clsx('text-[10px] font-mono', confColor)}>
                {(entry.response.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </button>

      {/* Remove button */}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove(entry.id)
        }}
        className={clsx(
          'absolute right-3 top-1/2 -translate-y-1/2',
          'opacity-0 group-hover:opacity-100 transition-opacity',
          'p-1 rounded text-obsidian-600 hover:text-crimson-400'
        )}
      >
        <X size={11} />
      </button>
    </motion.div>
  )
}
