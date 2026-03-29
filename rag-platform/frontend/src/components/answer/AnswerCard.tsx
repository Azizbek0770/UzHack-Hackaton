import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  CheckCircle, AlertCircle, Info, Clock,
  Table2, AlignLeft, Hash, Network, Copy, Check,
} from 'lucide-react'
import clsx from 'clsx'
import { FinBotAvatar } from '../ui/FinBotAvatar'
import type { QueryResponse, QueryType, ConfidenceLevel } from '../../services/types'

interface AnswerCardProps {
  response: QueryResponse
  question: string
}

const QUERY_TYPE_CONFIG: Record<QueryType, { icon: React.ElementType; label: string; color: string }> = {
  table:     { icon: Table2,    label: 'Jadval javobi',      color: 'text-jade-400 bg-jade-500/10 border-jade-500/20' },
  numeric:   { icon: Hash,      label: 'Raqamli javob',      color: 'text-gold-400 bg-gold-500/10 border-gold-500/20' },
  textual:   { icon: AlignLeft, label: 'Matnli javob',       color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  multi_hop: { icon: Network,   label: "Ko'p bosqichli",     color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
}

const CONFIDENCE_CONFIG: Record<ConfidenceLevel, { color: string; barColor: string; icon: React.ElementType; label: string }> = {
  high:   { color: 'text-jade-400',    barColor: 'bg-gradient-to-r from-jade-500 to-jade-400',    icon: CheckCircle,  label: "Yuqori ishonch" },
  medium: { color: 'text-gold-400',    barColor: 'bg-gradient-to-r from-gold-500 to-gold-300',    icon: Info,         label: "O'rta ishonch"  },
  low:    { color: 'text-crimson-400', barColor: 'bg-gradient-to-r from-crimson-500 to-crimson-400', icon: AlertCircle, label: "Past ishonch"  },
}

export function AnswerCard({ response, question }: AnswerCardProps) {
  const [copied, setCopied] = useState(false)
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(true)

  const queryConfig = QUERY_TYPE_CONFIG[response.query_type]
  const confConfig  = CONFIDENCE_CONFIG[response.confidence_level]
  const ConfIcon    = confConfig.icon
  const QueryIcon   = queryConfig.icon

  // Word-by-word streaming effect
  useEffect(() => {
    const words = response.answer.split(' ')
    let idx = 0
    setDisplayedText('')
    setIsTyping(true)

    const timer = setInterval(() => {
      if (idx >= words.length) {
        setIsTyping(false)
        clearInterval(timer)
        return
      }
      setDisplayedText(prev => (prev ? prev + ' ' + words[idx] : words[idx]))
      idx++
    }, 18)

    return () => clearInterval(timer)
  }, [response.answer])

  const handleCopy = async () => {
    await navigator.clipboard.writeText(response.answer)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-3xl mx-auto"
    >
      <div className={clsx(
        'rounded-2xl border overflow-hidden',
        'bg-obsidian-900 border-obsidian-700',
        'shadow-[0_0_60px_rgba(0,0,0,0.4)]'
      )}>

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="px-6 py-4 border-b border-obsidian-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={clsx(
              'flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border',
              queryConfig.color
            )}>
              <QueryIcon size={11} />
              {queryConfig.label}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-xs text-obsidian-500">
              <Clock size={11} />
              {response.processing_time_ms.toFixed(0)} ms
            </span>

            <motion.button
              onClick={handleCopy}
              whileTap={{ scale: 0.92 }}
              className={clsx(
                'p-1.5 rounded-lg transition-colors',
                copied
                  ? 'text-jade-400 bg-jade-500/10'
                  : 'text-obsidian-500 hover:text-gray-300 hover:bg-obsidian-700'
              )}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </motion.button>
          </div>
        </div>

        {/* ── FinBot Label ─────────────────────────────────────────────────── */}
        <div className="px-6 pt-5 pb-2 flex items-center gap-2">
          <FinBotAvatar size={16} />
          <span className="text-[10px] font-mono text-gold-400/70 uppercase tracking-widest">
            FinBot javobi
          </span>
          {isTyping && (
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ repeat: Infinity, duration: 0.8 }}
              className="w-1.5 h-3.5 bg-gold-500 rounded-sm inline-block ml-1"
            />
          )}
        </div>

        {/* ── Answer Body ─────────────────────────────────────────────────── */}
        <div className="px-6 pb-5">
          <p className="text-[15px] leading-relaxed text-gray-100">
            <HighlightedAnswer text={displayedText} question={question} />
          </p>
        </div>

        {/* ── Confidence Bar ──────────────────────────────────────────────── */}
        <div className="px-6 pb-5">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <ConfIcon size={13} className={confConfig.color} />
              <span className={clsx('text-xs font-medium', confConfig.color)}>
                {confConfig.label}
              </span>
            </div>
            <span className="font-mono text-xs text-obsidian-500">
              {(response.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <div className="h-1.5 bg-obsidian-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${response.confidence * 100}%` }}
              transition={{ delay: 0.4, duration: 1.2, ease: [0.4, 0, 0.2, 1] }}
              className={clsx('h-full rounded-full', confConfig.barColor)}
            />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// ── Keyword Highlighter ───────────────────────────────────────────────────────

function HighlightedAnswer({ text, question }: { text: string; question: string }) {
  const keywords = question
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => w.length >= 4)
    .map((w) => w.replace(/[^\wа-яёА-ЯЁa-zA-Z']/g, ''))
    .filter(Boolean)

  if (keywords.length === 0) return <>{text}</>

  const pattern = new RegExp(`(${keywords.join('|')})`, 'gi')
  const parts = text.split(pattern)

  return (
    <>
      {parts.map((part, i) =>
        keywords.some((k) => k.toLowerCase() === part.toLowerCase()) ? (
          <mark key={i} className="bg-gold-500/15 text-gold-300 rounded px-0.5 not-italic">
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </>
  )
}
