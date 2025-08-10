import { cn } from '@/lib/utils'

type LogLevel = 'info' | 'warn' | 'error' | 'debug'

export function LogLevelBadge({ level }: { level: LogLevel }) {
  return (
    <div
      className={cn(
        'flex items-center justify-center p-1 rounded-md border min-w-[48px]',
        { 'bg-red-500/15 border-red-500/50': level === 'error' },
        { 'bg-amber-500/15 border-amber-500/50': level === 'warn' },
        { 'bg-sky-500/15 border-sky-500/50': level === 'info' },
        { 'bg-gray-500/15 border-gray-500/50': level === 'debug' }
      )}>
      <div
        className={cn(
          'size-1.5 rounded-full mr-1',
          { 'bg-red-500': level === 'error' },
          { 'bg-amber-500': level === 'warn' },
          { 'bg-sky-500': level === 'info' },
          { 'bg-gray-500': level === 'debug' }
        )}
      />
      <span
        className={cn(
          'text-[10px] uppercase font-mono block leading-none',
          { 'text-red-500/75': level === 'error' },
          { 'text-amber-500/75': level === 'warn' },
          { 'text-sky-500/75': level === 'info' },
          { 'text-gray-500/75': level === 'debug' }
        )}>
        {level}
      </span>
    </div>
  )
}
