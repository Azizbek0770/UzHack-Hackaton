import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, Sparkles, ChevronDown } from 'lucide-react'
import clsx from 'clsx'
import type { QueryRequest, DocType } from '../../services/types'

interface QueryInputProps {
  onSubmit: (request: QueryRequest) => void
  isLoading: boolean
  disabled?: boolean
}

const SUGGESTIONS = [
  "2023-yildagi sof foyda qancha bo'lgan?",
  "Jami aktivlar hajmi qancha?",
  "Asosiy faoliyat turi nima?",
  "Kapital va zaxiralar miqdori?",
  "Daromad ko'rsatkichlari dinamikasi?",
]

const DOC_TYPE_OPTIONS: { value: DocType | ''; label: string }[] = [
  { value: '', label: 'Barcha hujjatlar' },
  { value: 'financial_report', label: 'Moliyaviy hisobot' },
  { value: 'annual_report', label: 'Yillik hisobot' },
  { value: 'disclosure', label: "Ma'lumot oshkoraligi" },
]

export function QueryInput({ onSubmit, isLoading, disabled }: QueryInputProps) {
  const [question, setQuestion] = useState('')
  const [docType, setDocType] = useState<DocType | ''>('')
  const [debugMode, setDebugMode] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [question])

  const handleSubmit = () => {
    const q = question.trim()
    if (!q || isLoading || disabled) return
    onSubmit({
      question: q,
      doc_type_filter: docType as DocType || undefined,
      debug: debugMode,
      top_k: 5,
    })
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSuggestion = (s: string) => {
    setQuestion(s)
    textareaRef.current?.focus()
  }

  const canSubmit = question.trim().length >= 3 && !isLoading && !disabled

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* ── Main Input Card ─────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className={clsx(
          'relative rounded-2xl border transition-all duration-300',
          'bg-obsidian-900',
          canSubmit || question.length > 0
            ? 'border-gold-500/35 shadow-[0_0_50px_rgba(201,168,76,0.1)]'
            : 'border-obsidian-700'
        )}
      >
        {/* Focus glow */}
        <div className={clsx(
          'absolute inset-0 rounded-2xl transition-opacity duration-500 pointer-events-none',
          'bg-gradient-to-r from-gold-500/5 via-transparent to-gold-500/5',
          question.length > 0 ? 'opacity-100' : 'opacity-0'
        )} />

        {/* Textarea */}
        <div className="relative p-5 pb-3">
          <div className="flex gap-3 items-start">
            <div className="mt-1 shrink-0">
              {isLoading ? (
                <Loader2 size={18} className="text-gold-500 animate-spin" />
              ) : (
                <Search
                  size={18}
                  className={clsx(
                    'transition-colors duration-200',
                    question.length > 0 ? 'text-gold-500' : 'text-obsidian-500'
                  )}
                />
              )}
            </div>

            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Moliyaviy hujjatlar bo'yicha savol bering..."
              disabled={isLoading || disabled}
              rows={1}
              className={clsx(
                'flex-1 resize-none bg-transparent outline-none',
                'text-[15px] font-sans leading-relaxed',
                'placeholder:text-obsidian-500 text-gray-100',
                'min-h-[28px] max-h-[200px]',
                'disabled:cursor-not-allowed disabled:opacity-60'
              )}
            />
          </div>
        </div>

        {/* ── Options Row ─────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-obsidian-700">
          <div className="flex items-center gap-3">
            {/* Doc type filter */}
            <div className="relative">
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value as DocType | '')}
                className={clsx(
                  'bg-obsidian-800 border border-obsidian-600 rounded-lg',
                  'text-xs text-gray-400 px-3 py-1.5 pr-7',
                  'appearance-none cursor-pointer outline-none',
                  'hover:border-gold-500/30 transition-colors'
                )}
              >
                {DOC_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
            </div>

            {/* Debug toggle */}
            <button
              onClick={() => setDebugMode((v) => !v)}
              className={clsx(
                'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-all',
                debugMode
                  ? 'bg-gold-500/10 border-gold-500/30 text-gold-400'
                  : 'bg-obsidian-800 border-obsidian-600 text-gray-500 hover:border-obsidian-500'
              )}
            >
              <Sparkles size={11} />
              Debug
            </button>
          </div>

          {/* Submit button */}
          <motion.button
            onClick={handleSubmit}
            disabled={!canSubmit}
            whileTap={{ scale: 0.96 }}
            className={clsx(
              'flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold',
              'transition-all duration-200',
              canSubmit
                ? 'bg-gold-500 text-obsidian-950 hover:bg-gold-400 shadow-[0_0_20px_rgba(201,168,76,0.25)]'
                : 'bg-obsidian-700 text-obsidian-500 cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Tahlil qilinmoqda...
              </>
            ) : (
              <>
                <Search size={14} />
                Qidirish
              </>
            )}
          </motion.button>
        </div>
      </motion.div>

      {/* ── Suggestions ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {question.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="mt-4 flex flex-wrap gap-2 justify-center"
          >
            {SUGGESTIONS.map((s, i) => (
              <motion.button
                key={i}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 * i + 0.2 }}
                onClick={() => handleSuggestion(s)}
                whileHover={{ y: -2 }}
                className={clsx(
                  'text-xs px-3 py-1.5 rounded-full border transition-all duration-200',
                  'border-obsidian-700 text-obsidian-400',
                  'hover:border-gold-500/35 hover:text-gold-400 hover:bg-gold-500/6',
                  'cursor-pointer'
                )}
              >
                {s}
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hint */}
      <p className="text-center text-xs text-obsidian-600 mt-3">
        Enter — yuborish · Shift+Enter — yangi qator
      </p>
    </div>
  )
}
