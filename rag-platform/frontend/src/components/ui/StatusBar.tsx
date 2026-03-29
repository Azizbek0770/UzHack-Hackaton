import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Circle, Database, Brain, Cpu } from 'lucide-react'
import clsx from 'clsx'
import { api } from '../../services/api'
import type { PipelineStatus } from '../../services/types'

export function StatusBar() {
  const [status, setStatus] = useState<PipelineStatus | null>(null)
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    const check = async () => {
      try {
        const s = await api.getStatus()
        setStatus(s)
        setOnline(s.status === 'ready')
      } catch {
        setOnline(false)
      }
    }
    check()
    const interval = setInterval(check, 30_000) // refresh every 30s
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-center gap-4">
      {/* Online indicator */}
      <div className="flex items-center gap-1.5">
        <motion.div
          animate={online === true ? { scale: [1, 1.3, 1] } : {}}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
        >
          <Circle
            size={7}
            className={clsx(
              'fill-current',
              online === null
                ? 'text-obsidian-600'
                : online
                ? 'text-jade-500'
                : 'text-crimson-500'
            )}
          />
        </motion.div>
        <span className="text-xs text-obsidian-500">
          {online === null ? 'Connecting...' : online ? 'Online' : 'Offline'}
        </span>
      </div>

      {status && (
        <>
          <div className="h-3 w-px bg-obsidian-700" />

          {/* Text chunks */}
          <div className="flex items-center gap-1.5">
            <Database size={11} className="text-obsidian-600" />
            <span className="text-xs font-mono text-obsidian-500">
              {status.indexes.text_chunks.toLocaleString()} chunks
            </span>
          </div>

          <div className="h-3 w-px bg-obsidian-700" />

          {/* Model info */}
          <div className="flex items-center gap-1.5">
            <Brain size={11} className="text-obsidian-600" />
            <span className="text-xs text-obsidian-500">
              {status.config.llm_model}
            </span>
          </div>

          <div className="h-3 w-px bg-obsidian-700" />

          {/* Embedding model */}
          <div className="flex items-center gap-1.5">
            <Cpu size={11} className="text-obsidian-600" />
            <span className="text-xs text-obsidian-500 truncate max-w-[120px]">
              {status.config.embedding_model.split('/').pop()}
            </span>
          </div>
        </>
      )}
    </div>
  )
}
