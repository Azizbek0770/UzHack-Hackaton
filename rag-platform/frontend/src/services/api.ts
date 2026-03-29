import axios, { AxiosInstance, AxiosError } from 'axios'
import type { QueryRequest, QueryResponse, PipelineStatus } from './types'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

class APIService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 60_000, // 60s — LLM calls can be slow
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Response interceptor — normalize errors
    this.client.interceptors.response.use(
      (res) => res,
      (error: AxiosError) => {
        const message =
          (error.response?.data as { detail?: string })?.detail ??
          error.message ??
          'Unknown error'
        return Promise.reject(new Error(message))
      }
    )
  }

  /**
   * Submit a question to the RAG pipeline.
   */
  async query(request: QueryRequest): Promise<QueryResponse> {
    const { data } = await this.client.post<QueryResponse>('/query', request)
    return data
  }

  /**
   * Get pipeline status and index sizes.
   */
  async getStatus(): Promise<PipelineStatus> {
    const { data } = await this.client.get<PipelineStatus>('/status')
    return data
  }

  /**
   * Trigger document re-ingestion.
   */
  async triggerIngestion(): Promise<{ message: string }> {
    const { data } = await this.client.post('/ingest')
    return data
  }

  /**
   * Clear the query cache.
   */
  async clearCache(): Promise<{ message: string }> {
    const { data } = await this.client.delete('/cache')
    return data
  }

  /**
   * Health check.
   */
  async health(): Promise<{ status: string; pipeline_ready: boolean }> {
    const { data } = await this.client.get('/../../health')
    return data
  }
}

export const api = new APIService()
