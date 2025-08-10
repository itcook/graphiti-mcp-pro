import { FileCode } from 'lucide-react'

export function LogSourceBadge({ source }: { source: string }) {
  return (
    <div className='flex items-center space-x-[4px] w-fit'>
      <FileCode className='size-3 text-muted-foreground' />
      <span className='text-[10px] text-muted-foreground font-mono block leading-none'>
        {source}
      </span>
    </div>
  )
}
