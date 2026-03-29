import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, ServerCrash } from 'lucide-react'
import clsx from 'clsx'

// ── Loading Skeleton ──────────────────────────────────────────────────────────

export function LoadingSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full max-w-3xl mx-auto space-y-4"
    >
      {/* Answer card skeleton */}
      <div className="rounded-2xl border border-obsidian-700 bg-obsidian-900 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-obsidian-700 flex items-center gap-3">
          <SkeletonBlock className="w-32 h-6 rounded-full" />
          <div className="ml-auto flex gap-2">
            <SkeletonBlock className="w-20 h-5 rounded" />
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-3">
          <SkeletonBlock className="w-full h-4 rounded" />
          <SkeletonBlock className="w-5/6 h-4 rounded" />
          <SkeletonBlock className="w-4/6 h-4 rounded" />
          <div className="pt-1">
            <SkeletonBlock className="w-3/6 h-4 rounded" />
          </div>
        </div>

        {/* Confidence */}
        <div className="px-6 pb-5 space-y-2">
          <div className="flex justify-between">
            <SkeletonBlock className="w-28 h-4 rounded" />
            <SkeletonBlock className="w-10 h-4 rounded" />
          </div>
          <SkeletonBlock className="w-full h-1.5 rounded-full" />
        </div>
      </div>

      {/* Sources skeleton */}
      <div className="flex gap-2 flex-wrap">
        {[1, 2, 3].map((i) => (
          <SkeletonBlock key={i} className="w-48 h-14 rounded-xl" />
        ))}
      </div>

      {/* Pulsing status text */}
      <motion.div
        className="text-center"
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
      >
        <span className="text-xs text-obsidian-500">
          Анализируем документы...
        </span>
      </motion.div>
    </motion.div>
  )
}

function SkeletonBlock({ className }: { className: string }) {
  return (
    <div
      className={clsx(
        'shimmer-bg',
        className
      )}
    />
  )
}

// ── Error State ───────────────────────────────────────────────────────────────

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  const isNetworkError =
    message.toLowerCase().includes('network') ||
    message.toLowerCase().includes('fetch') ||
    message.toLowerCase().includes('503')

  const Icon = isNetworkError ? ServerCrash : AlertTriangle

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full max-w-3xl mx-auto"
    >
      <div className={clsx(
        'rounded-2xl border p-6',
        'bg-crimson-500/5 border-crimson-500/20'
      )}>
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-xl bg-crimson-500/10 shrink-0">
            <Icon size={18} className="text-crimson-400" />
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-crimson-300 mb-1">
              {isNetworkError ? 'Нет связи с сервером' : 'Ошибка запроса'}
            </h3>
            <p className="text-xs text-crimson-400/70 leading-relaxed">
              {message}
            </p>

            {isNetworkError && (
              <p className="mt-2 text-xs text-obsidian-500">
                Убедитесь, что backend запущен на{' '}
                <code className="font-mono text-obsidian-400">localhost:8000</code>
              </p>
            )}
          </div>

          {onRetry && (
            <button
              onClick={onRetry}
              className={clsx(
                'shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg',
                'text-xs font-medium text-crimson-400',
                'border border-crimson-500/20 hover:bg-crimson-500/10',
                'transition-colors'
              )}
            >
              <RefreshCw size={12} />
              Повторить
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

// ── Empty State ───────────────────────────────────────────────────────────────

export function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3, duration: 0.6 }}
      className="text-center py-12 space-y-3"
    >
      <div className="text-5xl mb-4">◈</div>
      <p className="text-sm text-obsidian-500">
        Задайте вопрос о финансах компании
      </p>
      <p className="text-xs text-obsidian-600">
        Поддерживаются запросы на русском и узбекском языках
      </p>
    </motion.div>
  )
}
