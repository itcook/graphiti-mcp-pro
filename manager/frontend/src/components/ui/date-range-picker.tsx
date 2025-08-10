import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { Calendar } from '@/components/ui/calendar'
import { addDays } from 'date-fns'
import { CalendarRange } from 'lucide-react'
import * as React from 'react'
import { type DateRange } from 'react-day-picker'
import { useLanguage } from '@/contexts/language-context'
import { formatDate } from '@/lib/utils'

export default function DateRangePicker({
  className,
  value,
  onChange,
}: {
  className?: React.HTMLAttributes<HTMLDivElement>['className']
  value?: DateRange
  onChange?: (date: DateRange | undefined) => void
}) {
  const [date, setDate] = React.useState<DateRange | undefined>(
    value || {
      from: addDays(new Date(), -1),
      to: new Date(),
    }
  )

  React.useEffect(() => {
    if (!onChange) return
    onChange(date)
  }, [date, onChange])

  const { t, language } = useLanguage()

  return (
    <div className={cn('grid gap-2', className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id='date'
            variant='outline'
            className={cn(
              'w-[222px] justify-start text-left font-normal',
              !date && 'text-muted-foreground'
            )}>
            <CalendarRange className='mr-2 h-4 w-4' />
            {date?.from ? (
              date.to ? (
                <>
                  {formatDate(date.from, language)} - {formatDate(date.to, language)}
                </>
              ) : (
                formatDate(date.from, language)
              )
            ) : (
              <span>{t('common.pickDateRange')}</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className='w-auto p-0' align='start'>
          <Calendar
            autoFocus
            mode='range'
            defaultMonth={date?.from}
            selected={date}
            onSelect={setDate}
            numberOfMonths={2}
            disabled={{
              after: new Date(),
            }}
          />
        </PopoverContent>
      </Popover>
    </div>
  )
}
