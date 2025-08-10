'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import RadioButtonGroup from '@/components/ui/radio-button-group'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import DateRangePicker from '@/components/ui/date-range-picker'
import { useLanguage } from '@/contexts/language-context'
import type { DateRange } from 'react-day-picker'
import { format, subDays, getWeek } from 'date-fns'
import { zhCN, enUS } from 'date-fns/locale'
import DatePicker from '@/components/ui/date-picker'
import DateWeekPicker, { type WeekData } from '@/components/ui/date-week-picker'
import { DateMonthPicker, type MonthData } from '@/components/ui/date-month-picker'
import { TokenUsageBarChart } from '@/components/token-usage-bar-chart'
import { TablePagination } from '@/components/ui/table-pagination'
import {
  useTokenUsage,
  useDailyStats,
  useWeeklyStats,
  useMonthlyStats,
} from '@/hooks/useTokenUsage'
import type { TokenUsage } from '@/api/types'

function TokenUsageTable(params: { data: TokenUsage[] }) {
  const { t, language } = useLanguage()
  const { data } = params
  return (
    <>
      {!data || data.length === 0 ? (
        <div className='flex justify-center py-8'>
          <div className='text-muted-foreground'>No data</div>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t('tokenUsage.record.time')}</TableHead>
              <TableHead>{t('tokenUsage.record.model')}</TableHead>
              <TableHead>{t('tokenUsage.record.episode')}</TableHead>
              <TableHead>{t('tokenUsage.record.responseModel')}</TableHead>
              <TableHead>{t('tokenUsage.record.inputTokens')}</TableHead>
              <TableHead>{t('tokenUsage.record.outputTokens')}</TableHead>
              <TableHead>{t('tokenUsage.record.totalTokens')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.id}>
                <TableCell className='font-mono text-xs text-neutral-400'>
                  {format(
                    new Date(row.created_at),
                    language === 'zh-CN' ? 'yyyy/MM/dd HH:mm:ss' : 'MM/dd/yyyy HH:mm:ss'
                  )}
                </TableCell>
                <TableCell>{row.llm_model_name}</TableCell>
                <TableCell>{row.episode_name}</TableCell>
                <TableCell>{row.response_model}</TableCell>
                <TableCell className='font-mono'>{row.prompt_tokens.toLocaleString()}</TableCell>
                <TableCell className='font-mono'>
                  {row.completion_tokens.toLocaleString()}
                </TableCell>
                <TableCell className='font-mono'>{row.total_tokens.toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  )
}

export function TokenUsage() {
  const { t, language } = useLanguage()
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day')
  const now = new Date()
  const [selectedDay, setSelectedDay] = useState<Date | undefined>(now)
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange | undefined>({
    from: subDays(now, 1),
    to: now,
  })

  const today = format(now, 'yyyy-MM-dd')
  const currentWeek = getWeek(now, { weekStartsOn: 1 })
  const currentMonth = now.getMonth()
  const currentYear = now.getFullYear()

  const locale = language === 'zh-CN' ? zhCN : enUS
  const weekNumber = getWeek(now, { locale })

  const [selectedWeek, setSelectedWeek] = useState<WeekData | undefined>({
    year: now.getFullYear(),
    week: weekNumber,
  })

  const [selectedMonth, setSelectedMonth] = useState<MonthData | undefined>({
    year: now.getFullYear(),
    month: now.getMonth(),
  })

  // Prepare statistics query parameters
  const dayParam = selectedDay ? format(selectedDay, 'yyyy-MM-dd') : today
  const weekParam = selectedWeek?.week || currentWeek
  const weekYearParam = selectedWeek?.year || currentYear
  const monthParam = selectedMonth ? selectedMonth.month + 1 : currentMonth // Frontend months are 0-11, backend are 1-12
  const monthYearParam = selectedMonth?.year || currentYear

  // Get statistics data
  const { dailyStats, isLoading: isDailyLoading } = useDailyStats(dayParam)
  const { weeklyStats, isLoading: isWeeklyLoading } = useWeeklyStats(weekParam, weekYearParam)
  const { monthlyStats, isLoading: isMonthlyLoading } = useMonthlyStats(monthParam, monthYearParam)

  const {
    tokenUsage,
    total,
    isLoading: isTableLoading,
    update,
    page,
    pageSize,
  } = useTokenUsage(selectedDateRange)

  // Get corresponding chart data based on selected period
  const chartData = useMemo(() => {
    let statsData
    let isLoading = false

    switch (period) {
      case 'day':
        statsData = dailyStats
        isLoading = isDailyLoading
        break
      case 'week':
        statsData = weeklyStats
        isLoading = isWeeklyLoading
        break
      case 'month':
        statsData = monthlyStats
        isLoading = isMonthlyLoading
        break
    }

    if (isLoading || !statsData) {
      return null
    }

    // Convert to frontend required format
    return {
      period: statsData.period,
      completion_tokens: statsData.completion_tokens,
      prompt_tokens: statsData.prompt_tokens,
      total_tokens: statsData.total_tokens,
      details: statsData.details,
    }
  }, [
    period,
    dailyStats,
    weeklyStats,
    monthlyStats,
    isDailyLoading,
    isWeeklyLoading,
    isMonthlyLoading,
  ])

  function PeriodController() {
    return (
      <div className='flex items-center gap-2 ml-8'>
        <RadioButtonGroup
          value={period}
          onChange={(value) => setPeriod(value)}
          options={[
            { label: t('tokenUsage.byDay'), value: 'day' },
            { label: t('tokenUsage.byWeek'), value: 'week' },
            { label: t('tokenUsage.byMonth'), value: 'month' },
          ]}
        />
        {period === 'day' && <DatePicker value={selectedDay} onChange={setSelectedDay} />}
        {period === 'week' && <DateWeekPicker value={selectedWeek} onChange={setSelectedWeek} />}
        {period === 'month' && (
          <DateMonthPicker value={selectedMonth} onChange={setSelectedMonth} />
        )}
      </div>
    )
  }

  return (
    <div className='space-y-6'>
      {/* Chart */}
      {chartData ? (
        <TokenUsageBarChart data={chartData} Title={<PeriodController />} />
      ) : (
        <Card className='pt-0'>
          <CardHeader className='flex flex-row items-stretch justify-between border-b !p-0'>
            <PeriodController />
            <div className='flex items-center'>
              <div className='relative z-30 flex flex-1 flex-col justify-center gap-1 border-t px-6 py-4 text-left'>
                <span className='text-muted-foreground text-xs'>Loading...</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className='flex justify-center py-8'>
              <div className='text-muted-foreground'>Loading chart data...</div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>{t('tokenUsage.details')}</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Filter */}
          <div className='flex items-center gap-4 mb-4'>
            <DateRangePicker value={selectedDateRange} onChange={setSelectedDateRange} />
            {/* <Button variant='outline'>{t('tokenUsage.filter')}</Button> */}
          </div>

          {isTableLoading ? (
            <div className='flex justify-center py-8'>
              <div className='text-muted-foreground'>Loading...</div>
            </div>
          ) : (
            <>
              <TokenUsageTable data={tokenUsage} />

              {/* Pagination */}
              <TablePagination
                total={total}
                page={page}
                pageSize={pageSize}
                onChange={({ page, pageSize }) => {
                  update({ page })
                  update({ pageSize })
                }}
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
