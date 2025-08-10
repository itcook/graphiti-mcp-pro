// Base API response types
export interface ApiResponse<T = any> {
  data?: T
  message?: string
  status?: string
}

// Pagination types
export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// Settings types
export interface Setting {
  id: number
  llm_base_url: string
  llm_api_key: string
  llm_model_name: string
  small_llm_base_url?: string
  small_llm_api_key?: string
  small_llm_model_name?: string
  llm_temperature: number
  embedding_base_url?: string
  embedding_api_key?: string
  embedding_model_name?: string
  neo4j_uri: string
  neo4j_user: string
  neo4j_password: string
  semaphore_limit: number
  log_save_days: number
  clean_logs_at_hour: number
  enable_sync_return: boolean
}

export interface SettingUpdate {
  llm_base_url?: string
  llm_api_key?: string
  llm_model_name?: string
  small_llm_base_url?: string
  small_llm_api_key?: string
  small_llm_model_name?: string
  llm_temperature?: number
  embedding_base_url?: string
  embedding_api_key?: string
  embedding_model_name?: string
  neo4j_uri?: string
  neo4j_user?: string
  neo4j_password?: string
  semaphore_limit?: number
  log_save_days?: number
  clean_logs_at_hour?: number
  enable_sync_return?: boolean
}

// Log types
export interface LogEntry {
  id: string
  timestamp: string // ISO format string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  source?: string
}

export interface LogHistoryParams extends PaginationParams {
  level?: string
  search?: string
  start_time?: string // ISO format string
  end_time?: string // ISO format string
}

export interface LogLevelsResponse {
  levels: string[]
}

// Token usage types
export interface TokenUsage {
  id: number
  llm_model_name: string
  episode_name: string
  response_model: string
  completion_tokens: number
  prompt_tokens: number
  total_tokens: number
  created_at: string // ISO format string
}

export interface TokenUsageParams extends PaginationParams {
  start_date?: string // ISO format string
  end_date?: string // ISO format string
}

// Token usage statistics types
export interface TokenStats {
  total_tokens: number
  completion_tokens: number
  prompt_tokens: number
}

export interface StatPeriod {
  year?: number
  month?: number
  week?: number
  day?: number
  hour?: number
}

export type StatDetail = TokenStats & {
  period: StatPeriod
  details: Array<TokenStats & { period: string }>
}

// Service control types
export type MCPControlAction = 'start' | 'stop' | 'restart'
export type MCPStatus = 'running' | 'stopped' | 'starting' | 'stopping'

export interface MCPStatusResponse {
  status: MCPStatus
}

export interface MCPControlRequest {
  action: MCPControlAction
}

export type MCPControlResponse = {
  success: boolean
  action: string
} & MCPStatusResponse

// Error types
export interface ApiError {
  message: string
  status?: number
  code?: string
}
