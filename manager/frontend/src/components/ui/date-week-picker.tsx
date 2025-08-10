'use client'

import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { cn } from '@/lib/utils'
import { CalendarMinus2 } from 'lucide-react'
import * as React from 'react'
import { useLanguage } from '@/contexts/language-context'
import { startOfWeek, endOfWeek, getWeek, getYear, setWeek, format } from 'date-fns'
import { DateRange, rangeIncludesDate as isDateInRange } from 'react-day-picker'

// Custom function: check if date is within range

export interface WeekData {
  year: number
  week: number
}

export interface DateWeekPickerProps {
  value?: WeekData
  onChange?: (weekData: WeekData | undefined) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function DateWeekPicker({
  value,
  onChange,
  placeholder,
  disabled = false,
  className,
}: DateWeekPickerProps) {
  const { t, language } = useLanguage()
  const [open, setOpen] = React.useState(false)
  const [selectedWeek, setSelectedWeek] = React.useState<DateRange | undefined>()

  // Initialize selected week based on value
  React.useEffect(() => {
    if (value) {
      try {
        // Create first day of the year, then set to specified week
        let date = new Date(value.year, 0, 1)
        date = setWeek(date, value.week, { weekStartsOn: 1 }) // Week starts on Monday

        const weekStart = startOfWeek(date, { weekStartsOn: 1 })
        const weekEnd = endOfWeek(date, { weekStartsOn: 1 })

        setSelectedWeek({
          from: weekStart,
          to: weekEnd,
        })
      } catch (error) {
        console.error('Invalid week data:', error)
        setSelectedWeek(undefined)
      }
    } else {
      setSelectedWeek(undefined)
    }
  }, [value])

  // Handle date click
  const handleDayClick = (day: Date, modifiers: any) => {
    if (modifiers.selected) {
      setSelectedWeek(undefined)
      onChange?.(undefined)
      return
    }

    const weekStart = startOfWeek(day, { weekStartsOn: 1 })
    const weekEnd = endOfWeek(day, { weekStartsOn: 1 })

    const newWeekRange = {
      from: weekStart,
      to: weekEnd,
    }

    setSelectedWeek(newWeekRange)

    // Calculate year and week number
    const year = getYear(weekStart)
    const week = getWeek(weekStart, { weekStartsOn: 1, firstWeekContainsDate: 4 })

    onChange?.({ year, week })
  }

  // Format display text
  const getDisplayText = () => {
    if (!selectedWeek?.from || !selectedWeek?.to) {
      return placeholder || t?.('common.pickWeek') || '选择周'
    }

    const year = getYear(selectedWeek.from)
    const week = getWeek(selectedWeek.from, { weekStartsOn: 1, firstWeekContainsDate: 4 })
    const startDate = format(selectedWeek.from, language === 'zh-CN' ? 'MM/dd' : 'dd/MM')
    const endDate = format(selectedWeek.to, language === 'zh-CN' ? 'MM/dd' : 'dd/MM')

    if (language === 'zh-CN') {
      return `${year}年第${week}周 (${startDate} - ${endDate})`
    }

    return `Week ${week} of ${year} (${startDate} - ${endDate})`
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant='outline'
          disabled={disabled}
          className={cn(
            'justify-start text-left font-normal',
            !selectedWeek && 'text-muted-foreground',
            className
          )}>
          <CalendarMinus2 className='mr-2 h-4 w-4' />
          {getDisplayText()}
        </Button>
      </PopoverTrigger>
      <PopoverContent className='w-auto p-0' align='start'>
        <Calendar
          mode='single'
          showWeekNumber
          weekStartsOn={1}
          firstWeekContainsDate={4}
          showOutsideDays
          modifiers={{
            selected: selectedWeek,
            range_start: selectedWeek?.from,
            range_end: selectedWeek?.to,
            range_middle: (date: Date) =>
              selectedWeek ? isDateInRange(selectedWeek, date, true) : false,
          }}
          onDayClick={handleDayClick}
          disabled={{
            after: new Date(),
          }}
        />
      </PopoverContent>
    </Popover>
  )
}

export default DateWeekPicker
