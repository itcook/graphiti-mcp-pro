import { alovaInstance } from './alova/client'
import type { TokenUsage, StatDetail, PaginatedResponse, TokenUsageParams } from './types'

/**
 * Get paginated token usage records
 */

export const getTokenUsage = (params: TokenUsageParams) => {
  return alovaInstance.Get<PaginatedResponse<TokenUsage>>('/api/token-usage', {
    name: 'getTokenUsage',
    params,
  })
}

/**
 * Get daily token usage statistics
 */
export const getDailyStats = (day?: string) => {
  const params = day ? { day } : {}
  return alovaInstance.Get<StatDetail>('/api/token-usage/stats/daily', {
    name: 'getDailyStats',
    params,
  })
}

/**
 * Get weekly token usage statistics
 */
export const getWeeklyStats = (week?: number, year?: number) => {
  const params: { week?: number; year?: number } = {}
  if (week !== undefined) params.week = week
  if (year !== undefined) params.year = year

  return alovaInstance.Get<StatDetail>('/api/token-usage/stats/weekly', {
    name: 'getWeeklyStats',
    params,
  })
}

/**
 * Get monthly token usage statistics
 */
export const getMonthlyStats = (month?: number, year?: number) => {
  const params: { month?: number; year?: number } = {}
  if (month !== undefined) params.month = month
  if (year !== undefined) params.year = year

  return alovaInstance.Get<StatDetail>('/api/token-usage/stats/monthly', {
    name: 'getMonthlyStats',
    params,
  })
}
