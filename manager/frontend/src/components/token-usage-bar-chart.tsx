import * as React from 'react'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { Bar, BarChart, XAxis, YAxis } from 'recharts'
import { useLanguage } from '@/contexts/language-context'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { StatDetail } from '@/api'
import { formatUsageValue } from '@/utils/usageValueFormatter'

export function TokenUsageBarChart({ data, Title }: { data: StatDetail; Title: React.ReactNode }) {
  const { t } = useLanguage()
  const chartConfig = {
    prompt_tokens: {
      label: t('tokenUsage.char.inputTokens'),
      color: 'var(--chart-1)',
    },
    completion_tokens: {
      label: t('tokenUsage.char.outputTokens'),
      color: 'var(--chart-2)',
    },
  }

  const totalTokens = [
    {
      name: 'prompt_tokens',
      value: data.prompt_tokens,
    },
    {
      name: 'completion_tokens',
      value: data.completion_tokens,
    },
    {
      name: 'total_tokens',
      value: data.total_tokens,
    },
  ]

  return (
    <Card className='pt-0'>
      <CardHeader className='flex flex-row items-stretch justify-between border-b !p-0'>
        {Title}
        <div className='flex items-center'>
          {totalTokens.map((token) => {
            return (
              <div
                key={token.name}
                className='relative z-30 flex flex-1 flex-col justify-center gap-1 border-t px-6 py-4 text-left min-w-[148px] even:border-l sm:border-t-0 sm:border-l sm:px-8 sm:py-6'>
                <span className='text-muted-foreground text-xs'>
                  {token.name === 'prompt_tokens'
                    ? t('tokenUsage.char.inputTokens')
                    : token.name === 'completion_tokens'
                    ? t('tokenUsage.char.outputTokens')
                    : t('tokenUsage.record.totalTokens')}
                </span>
                <span className='text-lg font-mono leading-none font-bold sm:text-3xl'>
                  {formatUsageValue(token.value)}
                </span>
              </div>
            )
          })}
        </div>
      </CardHeader>
      <CardContent>
        <div className='w-full h-[320px]'>
          {data.details.length === 0 ? (
            <div className='h-full flex justify-center items-center'>
              <div className='text-muted-foreground'>No data</div>
            </div>
          ) : (
            <ChartContainer config={chartConfig} className='h-[320px] w-full'>
              <BarChart data={data.details}>
                <XAxis dataKey='period' tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      className='min-w-[200px]'
                      formatter={(value, name, item, index) => (
                        <>
                          <div
                            className='h-2.5 w-2.5 shrink-0 rounded-[2px] bg-[--color-bg]'
                            style={
                              {
                                '--color-bg': `var(--color-${name})`,
                              } as React.CSSProperties
                            }
                          />
                          {chartConfig[name as keyof typeof chartConfig]?.label || name}
                          <div className='ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums text-foreground'>
                            {value}
                          </div>
                          {/* Add this after the last item */}
                          {index === 1 && (
                            <div className='mt-1.5 flex basis-full items-center border-t pt-1.5 text-xs font-medium text-foreground'>
                              {t('tokenUsage.record.totalTokens')}
                              <div className='ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums text-foreground'>
                                {item.payload.total_tokens}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    />
                  }
                />
                <Bar dataKey='prompt_tokens' stackId='a' fill='var(--chart-1)' />
                <Bar dataKey='completion_tokens' stackId='a' fill='var(--chart-2)' />
              </BarChart>
            </ChartContainer>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
