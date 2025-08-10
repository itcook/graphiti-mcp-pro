import { useState, useCallback } from 'react'
import { useRequest, usePagination, useSSE } from 'alova/client'
import { getLogHistory, getLogLevels, getRealtimeLogs } from '../api/logs'
import type { LogEntry } from '../api/types'
import type { DateRange } from 'react-day-picker'
import { format } from 'date-fns'
import { logger } from '@/utils/logger'

/**
 * Hook for managing log history
 */
export const useLogHistory = (level?: string, search?: string, dateRange?: DateRange) => {
  const { from, to } = dateRange || {}
  const start_time = from ? format(from, 'yyyy-MM-dd') : undefined
  const end_time = to ? format(to, 'yyyy-MM-dd') : undefined
  const { data, page, pageSize, total, update, error } = usePagination(
    (page, pageSize) =>
      getLogHistory({
        page,
        page_size: pageSize,
        level,
        search,
        start_time,
        end_time,
      }),
    {
      initialData: {
        total: 0,
        data: [],
      },
      initialPage: 1,
      initialPageSize: 20,
      watchingStates: [level, search, dateRange],
      data: (res) => res.items,
      total: (res) => res.total,
    }
  )

  return {
    logs: data || [],
    total: total || 0,
    page: page || 1,
    pageSize: pageSize || 20,
    update,
    error,
  }
}

/**
 * Hook for getting log levels
 */
export const useLogLevels = () => {
  const {
    data: levelsData,
    loading: isLoading,
    error,
  } = useRequest(getLogLevels, {
    immediate: true,
  })

  return {
    levels: levelsData?.levels || [],
    isLoading,
    error,
  }
}

/**
 * Hook for real-time log streaming
 */
export const useRealtimeLogs = (level?: string, search?: string) => {
  const [realtimeLogs, setRealtimeLogs] = useState<LogEntry[]>([])

  // Create SSE connection using Alova
  const { eventSource, readyState, onMessage, onError, onOpen, send, close } = useSSE(
    () => getRealtimeLogs(level, search),
    {
      immediate: true,
      interceptByGlobalResponded: false,
      initialData: [],
    }
  )

  // Handle incoming messages
  onMessage(({ data: messageData }) => {
    try {
      const logData = typeof messageData === 'string' ? JSON.parse(messageData) : messageData
      if (logData && !logData.error) {
        setRealtimeLogs((prev) => [...prev, logData].slice(-100)) // Keep only latest 100 logs
      }
    } catch (error) {
      logger.error('Failed to parse log event data:', error)
    }
  })

  // Handle connection open
  onOpen(() => {
    logger.log('SSE connection opened')
  })

  // Handle errors with auto-reconnect
  onError(({ error }) => {
    logger.error('SSE error:', error)

    // Auto reconnect after 3 seconds
    setTimeout(() => {
      if (readyState === 2) {
        // EventSource.CLOSED
        connect()
      }
    }, 3000)
  })

  const connect = useCallback(() => {
    send()
  }, [send])

  const disconnect = useCallback(() => {
    close()
    setRealtimeLogs([])
  }, [close])

  const clearLogs = useCallback(() => {
    setRealtimeLogs([])
  }, [])

  return {
    realtimeLogs,
    isConnected: readyState === 1, // EventSource.OPEN
    connectionError: readyState === 2 ? 'Connection lost. Attempting to reconnect...' : null,
    readyState,
    eventSource,
    connect,
    disconnect,
    clearLogs,
  }
}
