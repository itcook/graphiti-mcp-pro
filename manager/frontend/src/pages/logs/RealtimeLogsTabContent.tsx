import { useRef } from 'react'
import { useLanguage } from '@/contexts/language-context'
import { useCardContentHeight, useScrollToBottom } from '@/pages/logs/hooks'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Play, Pause, Trash2 } from 'lucide-react'
import { LogItem } from './LogItem'
import { useRealtimeLogs } from '@/hooks/useLogs'

export default function RealtimeLogsTabContent() {
  const { t } = useLanguage()
  const RealtimeCardRef = useRef<HTMLDivElement>(null)
  const cardContentHeight = useCardContentHeight(RealtimeCardRef)
  const realTimeScrollRef = useRef<HTMLDivElement>(null)

  // Use realtime logs hook
  const { realtimeLogs, isConnected, connectionError, connect, disconnect, clearLogs } =
    useRealtimeLogs()

  useScrollToBottom(realTimeScrollRef, realtimeLogs)

  return (
    <Card className='h-full' innerRef={RealtimeCardRef}>
      <CardHeader className='border-b'>
        <div className='flex items-center mb-4 gap-2'>
          <Button
            variant='outline'
            size='sm'
            onClick={() => (isConnected ? disconnect() : connect())}>
            {isConnected ? (
              <>
                <Pause className='h-4 w-4 mr-2' />
                {t('logs.pause')}
              </>
            ) : (
              <>
                <Play className='h-4 w-4 mr-2' />
                {t('logs.start')}
              </>
            )}
          </Button>
          <Button variant='outline' size='sm' onClick={clearLogs}>
            <Trash2 className='h-4 w-4 mr-2' />
            {t('logs.clear')}
          </Button>
        </div>
      </CardHeader>
      <CardContent style={{ height: cardContentHeight }}>
        <ScrollArea style={{ height: cardContentHeight }}>
          {connectionError && (
            <div className='flex items-center justify-center h-16 text-red-500 text-sm'>
              {connectionError}
            </div>
          )}
          {realtimeLogs.length === 0 ? (
            <div className='flex items-center justify-center h-32 text-muted-foreground'>
              {isConnected ? t('logs.waitingData') : t('logs.paused')}
            </div>
          ) : (
            <div ref={realTimeScrollRef}>
              {realtimeLogs.map((log) => (
                <LogItem key={log.id} log={log} />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
