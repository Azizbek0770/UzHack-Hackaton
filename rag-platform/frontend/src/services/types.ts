// Domain types — mirror backend Pydantic schemas

export type QueryType = 'numeric' | 'textual' | 'table' | 'multi_hop'
export type ConfidenceLevel = 'high' | 'medium' | 'low'
export type DocType =
  | 'financial_report'
  | 'annual_report'
  | 'disclosure'
  | 'metadata'
  | 'unknown'

export interface SourceReference {
  file: string
  page: number | null
  sheet: string | null
  company: string
  doc_type: string
  chunk_type: string
  excerpt: string | null
}

export interface DebugChunk {
  source: string
  score: number
  type: string
  excerpt: string
}

export interface DebugInfo {
  query_type: QueryType
  rewritten_query: string | null
  retrieved_text_chunks: number
  retrieved_table_chunks: number
  stage_timings: Record<string, number>
  top_chunks: DebugChunk[]
}

export interface QueryResponse {
  answer: string
  confidence: number
  confidence_level: ConfidenceLevel
  query_type: QueryType
  processing_time_ms: number
  relevant_chunks: SourceReference[]
  debug: DebugInfo | null
}

export interface QueryRequest {
  question: string
  company_filter?: string
  doc_type_filter?: DocType | null
  debug?: boolean
  top_k?: number
}

export interface PipelineStatus {
  status: string
  indexes: {
    text_chunks: number
    table_chunks: number
    bm25_docs: number
  }
  cache: {
    enabled: boolean
    size: number
    max_size: number
  }
  config: {
    embedding_model: string
    llm_model: string
    llm_provider: string
    retrieval_top_k: number
    final_top_k: number
  }
}

// ── Query History Entry ───────────────────────────────────────────────────────

export interface HistoryEntry {
  id: string
  question: string
  response: QueryResponse
  timestamp: Date
}
