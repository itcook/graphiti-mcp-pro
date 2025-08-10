'use client'

import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { Calendar } from '@/components/ui/calendar'
import { formatDate } from '@/lib/utils'
import { CalendarIcon } from 'lucide-react'
import * as React from 'react'
import { useLanguage } from '@/contexts/language-context'

export default function DatePicker({
  value,
  onChange,
}: {
  value?: Date
  onChange?: (date: Date | undefined) => void
}) {
  const [date, setDate] = React.useState<Date>(value || new Date())
  const { t, language } = useLanguage()

  React.useEffect(() => {
    if (!onChange) return
    onChange(date)
  }, [date, onChange])

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant='outline'
          className={cn('justify-start text-left font-normal', !date && 'text-muted-foreground')}>
          <CalendarIcon className='mr-2 h-4 w-4' />
          {date ? formatDate(date, language) : <span>{t('common.pickDate')}</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className='w-auto p-0' align='start'>
        <Calendar
          mode='single'
          required
          selected={date}
          onSelect={setDate}
          disabled={{
            after: new Date(),
          }}
        />
      </PopoverContent>
    </Popover>
  )
}
