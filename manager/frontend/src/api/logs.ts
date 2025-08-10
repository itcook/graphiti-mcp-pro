import { alovaInstance } from './alova/client'
import type { LogEntry, LogHistoryParams, LogLevelsResponse, PaginatedResponse } from './types'

/**
 * Get paginated log history
 */
export const getLogHistory = (params: LogHistoryParams) => {
  return alovaInstance.Get<PaginatedResponse<LogEntry>>('/api/logs/history', {
    name: 'getLogHistory',
    params,
  })
}

/**
 * Get available log levels
 */
export const getLogLevels = () => {
  return alovaInstance.Get<LogLevelsResponse>('/api/logs/levels', {
    name: 'getLogLevels',
  })
}

/**
 * Create SSE method for real-time logs using Alova
 */
export const getRealtimeLogs = (level?: string, search?: string) => {
  const params: Record<string, string> = {}

  if (level) {
    params.level = level
  }

  if (search) {
    params.search = search
  }

  return alovaInstance.Get<LogEntry>('/api/logs/realtime', {
    name: 'getRealtimeLogs',
    params,
  })
}
