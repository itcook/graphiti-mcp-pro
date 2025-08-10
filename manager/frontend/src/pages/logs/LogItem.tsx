import { LogLevelBadge } from '@/components/log-level-badge'
import { LogSourceBadge } from '@/components/LogSourceBadge'
import type { LogEntry } from '@/api/types'
import { useLanguage } from '@/contexts/language-context'
import { format } from 'date-fns'

type LogItemProps = { log: LogEntry }

export function LogItem({ log }: LogItemProps) {
  const { language } = useLanguage()

  return (
    <div className='flex items-start gap-2 p-3 border-b border-gray-400/15 last:border-b-0 hover:bg-muted/50'>
      <div className='flex items-center space-x-2'>
        <span className='text-xs text-muted-foreground font-mono block'>
          {format(
            new Date(log.timestamp),
            language === 'zh-CN' ? 'yyyy/MM/dd HH:mm:ss' : ' MM/dd/yyyy HH:mm:ss'
          )}
        </span>
        <LogLevelBadge level={log.level} />
      </div>
      <div className='flex-1 min-w-0 mt-[1px]'>
        <p className='text-xs break-words'>{log.message}</p>
      </div>
      {log.source && (
        <div className='mt-[4px]'>
          {' '}
          <LogSourceBadge source={log.source} />
        </div>
      )}
    </div>
  )
}
