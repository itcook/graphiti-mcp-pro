'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardAction } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Play, RefreshCcw, CheckCircle, XCircle, Clock, Power } from 'lucide-react'
import { toast } from 'sonner'
import { useLanguage } from '@/contexts/language-context'
import { toastConfig } from '@/lib/utils'
import { TokenUsageBarChart } from '@/components/token-usage-bar-chart'
import { MCPConfigCodeBlock } from '@/components/mcp-config-code-block'
import { MCPServerStatus } from '@/components/mcp-server-status'
import { useDailyStats, useMCPHealth, useMCPStatusStream, useMCPControl } from '@/hooks'
import type { MCPStatus } from '@/api/types'

export function Home() {
  const { status: initStatus } = useMCPHealth()
  const [serviceStatus, setServiceStatus] = useState<MCPStatus>(initStatus)
  const { t } = useLanguage()

  useMCPStatusStream(setServiceStatus)

  const { handleControl: start } = useMCPControl('start')
  const { handleControl: stop } = useMCPControl('stop')
  const { handleControl: restart } = useMCPControl('restart')

  const getStatusIcon = () => {
    switch (serviceStatus) {
      case 'running':
        return <CheckCircle className='h-4 w-4 text-green-500' />
      case 'stopped':
        return <XCircle className='h-4 w-4 text-red-500' />
      case 'starting':
        return <Clock className='h-4 w-4 text-yellow-500 animate-spin' />
      case 'stopping':
        return <Clock className='h-4 w-4 text-yellow-500 animate-spin' />
    }
  }

  const { dailyStats, error } = useDailyStats()

  if (error) {
    toast.error('Failed to fetch token usage data', toastConfig)
  }

  // const { data: healthData } = useMCPHealth()
  // const { status } = useMCPStatusStream()

  return (
    <div className='space-y-6'>
      {/* First row: Service status and configuration information */}
      {/* Service status card */}
      <Card>
        <CardHeader className='flex items-center justify-between'>
          <CardTitle className='flex items-center gap-2'>
            {getStatusIcon()}
            {t('home.graphitiMCPService')}
            <MCPServerStatus status={serviceStatus} />
          </CardTitle>
          <CardAction>
            <div className='flex gap-4'>
              <Button
                variant='ghost'
                onClick={() => start()}
                disabled={serviceStatus !== 'stopped'}
                size='sm'>
                <Play className='h-4 w-4 mr-2' />
                {t('home.start')}
              </Button>
              <Button
                onClick={() => restart()}
                disabled={serviceStatus !== 'running'}
                variant='ghost'
                size='sm'>
                <RefreshCcw className='h-4 w-4 mr-2' />
                {t('home.restart')}
              </Button>
              <Button
                onClick={() => stop()}
                disabled={serviceStatus !== 'running'}
                variant='ghost'
                size='sm'>
                <Power className='h-4 w-4 mr-2' />
                {t('home.stop')}
              </Button>
            </div>
          </CardAction>
        </CardHeader>
        <CardContent>
          <MCPConfigCodeBlock />
        </CardContent>
      </Card>

      {/* Today's TOKEN consumption */}
      {dailyStats && (
        <TokenUsageBarChart
          data={dailyStats}
          Title={
            <div className='flex flex-1 flex-col justify-center gap-1 px-6 pt-4 pb-3 sm:!py-0'>
              <CardTitle>{t('home.tokenUsage')}</CardTitle>
            </div>
          }
        />
      )}
    </div>
  )
}
