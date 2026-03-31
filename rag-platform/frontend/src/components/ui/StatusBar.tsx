import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Circle, Database, Brain, Cpu } from 'lucide-react'
import clsx from 'clsx'
import { api } from '../../services/api'
import type { PipelineStatus } from '../../services/types'

export function StatusBar() {
  const [status, setStatus] = useState<PipelineStatus | null>(null)
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    let mounted = true

    const check = async () => {
      try {
        const s = await api.getStatus()
        if (!mounted) return
        setStatus(s)
        setOnline(s.status === 'ready')
      } catch {
        if (!mounted) return
        setOnline(false)
      }
    }

    check()
    const interval = setInterval(check, 30_000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const isLoading = online === null

  const embeddingName = useMemo(() => {
    return status?.config.embedding_model?.split('/').pop()
  }, [status])

  return (
    <div className="flex items-center gap-3 px-3 py-1.5 rounded-xl bg-obsidian-900/60 backdrop-blur-md border border-white/5 shadow-sm">

      {/* STATUS */}
      <div className="flex items-center gap-2">
        <motion.div
          animate={
            online
              ? { scale: [1, 1.4, 1], opacity: [0.8, 1, 0.8] }
              : { scale: 1 }
          }
          transition={{ repeat: Infinity, duration: 2 }}
          className="relative"
        >
          <Circle
            size={8}
            className={clsx(
              'fill-current',
              isLoading
                ? 'text-obsidian-500'
                : online
                ? 'text-jade-400'
                : 'text-red-500'
            )}
          />

          {/* glow */}
          {online && (
            <span className="absolute inset-0 rounded-full bg-jade-400 blur-sm opacity-40" />
          )}
        </motion.div>

        <span className="text-sm font-semibold">
          {isLoading ? 'Ulanmoqda...' : online ? 'Onlayn' : 'Oflayn'}
        </span>
      </div>

      {/* DATA */}
      <AnimatePresence>
        {status && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-4 text-[11px] text-obsidian-400"
          >
            {/* TEXT CHUNKS */}
            <div className="flex items-center gap-1.5 hover:text-white transition">
              <Database size={12} />
              <span className="font-mono">
                {status.indexes.text_chunks.toLocaleString()}
              </span>
            </div>

            {/* MODEL */}
            <div className="flex items-center gap-1.5 hover:text-white transition">
              <Brain size={12} />
              <span>{status.config.llm_model}</span>
            </div>

            {/* EMBEDDING */}
            <div className="flex items-center gap-1.5 hover:text-white transition max-w-[120px] truncate">
              <Cpu size={12} />
              <span>{embeddingName}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}