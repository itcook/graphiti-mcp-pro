export interface TokenUsageStatsDetailData {
  period: string
  completion_tokens: number
  prompt_tokens: number
  total_tokens: number
}

export interface TokenUsageStatsData {
  period: {
    year: number
    month?: number
    week?: number
    day?: number
  }
  completion_tokens: number
  prompt_tokens: number
  total_tokens: number
  details: TokenUsageStatsDetailData[]
}

export interface LogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  source?: string
}
