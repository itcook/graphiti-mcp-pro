import { useWatcher, usePagination } from 'alova/client'
import { getTokenUsage, getDailyStats, getWeeklyStats, getMonthlyStats } from '../api/tokenUsage'
import type { DateRange } from 'react-day-picker'
import { format } from 'date-fns'

/**
 * Hook for managing token usage records
 */
export const useTokenUsage = (dateRange?: DateRange) => {
  const start_date = dateRange?.from ? format(dateRange.from, 'yyyy-MM-dd') : undefined
  const end_date = dateRange?.to ? format(dateRange.to, 'yyyy-MM-dd') : undefined
  const { loading, data, page, pageSize, pageCount, total, update, error } = usePagination(
    (page, pageSize) =>
      getTokenUsage({
        page,
        page_size: pageSize,
        start_date,
        end_date,
      }),
    {
      initialData: {
        total: 0,
        data: [],
      },
      initialPage: 1,
      initialPageSize: 20,
      watchingStates: [dateRange],
      data: (res) => res.items,
      total: (res) => res.total,
    }
  )

  return {
    tokenUsage: data || [],
    total: total || 0,
    page: page || 1,
    pageSize: pageSize || 20,
    pageCount: pageCount || 0,
    isLoading: loading,
    update,
    error,
  }
}

/**
 * Hook for daily token usage statistics
 */
export const useDailyStats = (day?: string) => {
  const {
    data: dailyStats,
    loading: isLoading,
    error,
    send: fetchDailyStats,
  } = useWatcher(() => getDailyStats(day), [day], {
    immediate: true,
  })

  return {
    dailyStats,
    isLoading,
    error,
    refetch: fetchDailyStats,
  }
}

/**
 * Hook for weekly token usage statistics
 */
export const useWeeklyStats = (week?: number, year?: number) => {
  const {
    data: weeklyStats,
    loading: isLoading,
    error,
    send: fetchWeeklyStats,
  } = useWatcher(() => getWeeklyStats(week, year), [week, year], {
    immediate: true,
  })

  return {
    weeklyStats,
    isLoading,
    error,
    refetch: fetchWeeklyStats,
  }
}

/**
 * Hook for monthly token usage statistics
 */
export const useMonthlyStats = (month?: number, year?: number) => {
  const {
    data: monthlyStats,
    loading: isLoading,
    error,
    send: fetchMonthlyStats,
  } = useWatcher(() => getMonthlyStats(month, year), [month, year], {
    immediate: true,
  })

  return {
    monthlyStats,
    isLoading,
    error,
    refetch: fetchMonthlyStats,
  }
}
