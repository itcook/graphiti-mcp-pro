import { Status, StatusIndicator, StatusLabel, type StatusProps } from './ui/shadcn-io/status'
import { useLanguage } from '@/contexts/language-context'
import { type MCPStatus } from '@/api/types'

export interface MCPServerStatusProps {
  status: MCPStatus
}

export function MCPServerStatus({ status }: MCPServerStatusProps) {
  const { t } = useLanguage()

  const statusMap: Record<MCPServerStatusProps['status'], StatusProps['status']> = {
    running: 'online',
    stopped: 'offline',
    starting: 'maintenance',
    stopping: 'maintenance',
  }

  return (
    <Status status={statusMap[status]} className='rounded-full'>
      <StatusIndicator />
      <StatusLabel className='text-xs font-normal'>{t(`home.serverStatus.${status}`)}</StatusLabel>
    </Status>
  )
}
