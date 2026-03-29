import { useState, useCallback, useRef } from 'react'
import { api } from '../services/api'
import type { QueryRequest, QueryResponse, HistoryEntry } from '../services/types'

const MAX_HISTORY = 20

// ── useQuery ─────────────────────────────────────────────────────────────────

interface UseQueryState {
  response: QueryResponse | null
  isLoading: boolean
  error: string | null
}

export function useQuery() {
  const [state, setState] = useState<UseQueryState>({
    response: null,
    isLoading: false,
    error: null,
  })

  const abortRef = useRef<AbortController | null>(null)

  const submit = useCallback(async (request: QueryRequest) => {
    // Cancel any in-flight request
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setState({ response: null, isLoading: true, error: null })

    try {
      const response = await api.query(request)
      setState({ response, isLoading: false, error: null })
      return response
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Query failed'
      setState({ response: null, isLoading: false, error: message })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState({ response: null, isLoading: false, error: null })
  }, [])

  return { ...state, submit, reset }
}

// ── useQueryHistory ───────────────────────────────────────────────────────────

export function useQueryHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>([])

  const addEntry = useCallback((question: string, response: QueryResponse) => {
    const entry: HistoryEntry = {
      id: crypto.randomUUID(),
      question,
      response,
      timestamp: new Date(),
    }
    setHistory((prev) => [entry, ...prev].slice(0, MAX_HISTORY))
  }, [])

  const clearHistory = useCallback(() => setHistory([]), [])

  const removeEntry = useCallback((id: string) => {
    setHistory((prev) => prev.filter((e) => e.id !== id))
  }, [])

  return { history, addEntry, clearHistory, removeEntry }
}

// ── useDebounce ───────────────────────────────────────────────────────────────

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)

  useState(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  })

  return debounced
}
