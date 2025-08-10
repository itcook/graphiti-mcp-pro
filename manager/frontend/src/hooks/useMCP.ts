import { useCallback, useEffect } from 'react'
import { useRequest, useSSE } from 'alova/client'
import { getMCPServiceHealth, getMCPServiceStatus, controlMCPService } from '../api/mcp'
import { logger } from '@/utils/logger'
import { type MCPStatus, MCPControlAction } from '@/api/types'
import { toast } from 'sonner'
import { useLanguage } from '@/contexts/language-context'
import { toastConfig } from '@/lib/utils'

type Position =
  | 'top-left'
  | 'top-right'
  | 'bottom-left'
  | 'bottom-right'
  | 'top-center'
  | 'bottom-center'

export const useMCPControl = (action: MCPControlAction) => {
  const { t } = useLanguage()
  const loadingToastConfig = {
    id: `mcp-control-${action}-loading`,
    duration: 0,
    position: 'top-center' as Position,
  }

  const loadingMessage = (() => {
    switch (action) {
      case 'start':
        return t('common.toast.starting')
      case 'stop':
        return t('common.toast.stopping')
      case 'restart':
        return t('common.toast.restarting')
    }
  })()
  const successMessage = (() => {
    switch (action) {
      case 'start':
        return t('common.toast.started')
      case 'stop':
        return t('common.toast.stopped')
      case 'restart':
        return t('common.toast.restarted')
    }
  })()

  const { send, loading } = useRequest(() => controlMCPService({ action }), {
    immediate: false,
    debounce: 500,

    onSuccess: () => {
      toast.success(successMessage, toastConfig)
    },

    onError: () => {
      toast.error('Failed to control MCP service', toastConfig)
    },
  })

  useEffect(() => {
    if (loading) {
      toast.loading(loadingMessage, loadingToastConfig)
    } else {
      toast.dismiss(loadingToastConfig.id)
    }
  }, [loading])

  return { handleControl: send }
}

export const useMCPHealth = () => {
  const { loading, data, error } = useRequest(() => getMCPServiceHealth(), {
    immediate: true,
  })

  return {
    loading,
    status: data?.status,
    error,
  }
}

export const useMCPStatusStream = (statusSetter?: (status: MCPStatus) => void) => {
  const { eventSource, readyState, onMessage, onError, onOpen, send, close } = useSSE(
    getMCPServiceStatus(),
    {
      immediate: true,
      interceptByGlobalResponded: false,
    }
  )

  onMessage(({ data: messageData }) => {
    try {
      const eventData = typeof messageData === 'string' ? JSON.parse(messageData) : messageData
      if (eventData && eventData.status) {
        if (statusSetter) {
          statusSetter(eventData.status)
        }
      }
    } catch (error) {
      logger.error('Failed to parse status event data:', error)
    }
  })

  onOpen(() => {
    logger.log('Status SSE connection opened')
  })

  onError(({ error }) => {
    logger.error('Status SSE error:', error)

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
    logger.log('Status SSE connection closed')
  }, [close])

  return {
    isConnected: readyState === 1, // EventSource.OPEN
    connectionError: readyState === 2 ? 'Status Connection lost. Attempting to reconnect...' : null,
    readyState,
    eventSource,
    connect,
    disconnect,
  }
}
