import { useState, useRef } from 'react'
import { useLanguage } from '@/contexts/language-context'
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { LogItem } from './LogItem'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import RadioButtonGroup from '@/components/ui/radio-button-group'
import { Search, CircleX } from 'lucide-react'
import { TablePagination } from '@/components/ui/table-pagination'
import { useCardContentHeight } from './hooks'
import { useLogHistory, useLogLevels } from '@/hooks/useLogs'

export default function HistoryLogsTabContent() {
  const { t } = useLanguage()
  const HistoryLogsCardRef = useRef<HTMLDivElement>(null)
  const cardContentHeight = useCardContentHeight(HistoryLogsCardRef)

  // Search state management
  const [searchInput, setSearchInput] = useState('') // Input field value
  const [searchQuery, setSearchQuery] = useState('') // Search term submitted to API
  const [levelFilter, setLevelFilter] = useState<string>() // Level filter

  // Use history logs hook
  const { logs, total, page, pageSize, update, error } = useLogHistory(levelFilter, searchQuery)

  // Use log levels hook
  const { levels } = useLogLevels()

  // Execute search
  const handleSearch = () => {
    setSearchQuery(searchInput)
    update({ page: 1 }) // Reset to first page when searching
  }

  // Clear search
  const clearSearch = () => {
    setSearchInput('')
    setSearchQuery('')
    update({ page: 1 })
  }

  // Handle level filter change
  const handleLevelChange = (value: string) => {
    const newLevel = value === 'all' ? undefined : value
    setLevelFilter(newLevel)
    update({ page: 1 })
  }

  // Handle pagination change
  const handlePageChange = ({
    page: newPage,
    pageSize: newPageSize,
  }: {
    page: number
    pageSize: number
  }) => {
    update({ page: newPage, pageSize: newPageSize })
  }

  return (
    <Card className='h-full' innerRef={HistoryLogsCardRef}>
      <CardHeader className='border-b'>
        {/* Filter */}
        <div className='flex items-center justify-between mb-4'>
          <RadioButtonGroup
            value={levelFilter || 'all'}
            onChange={handleLevelChange}
            options={[
              { label: t('logs.level.all'), value: 'all' },
              ...levels.map((level) => ({
                label: t(`logs.level.${level}`),
                value: level,
              })),
            ]}
          />

          <div className='flex items-center space-x-2'>
            <div className='relative'>
              <Search className='absolute left-2 top-2.5 h-4 w-4 text-muted-foreground' />
              <Input
                id='search'
                placeholder={t('logs.searchPlaceholder')}
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className='px-8'
              />
              {searchInput && (
                <CircleX
                  className='h-4 w-4 absolute right-2 top-2.5 stroke-muted-foreground cursor-pointer'
                  onClick={clearSearch}
                />
              )}
            </div>
            <Button size='default' variant='outline' onClick={handleSearch}>
              {t('logs.search')}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent style={{ height: cardContentHeight }}>
        <ScrollArea style={{ height: cardContentHeight }}>
          {error && (
            <div className='flex items-center justify-center h-16 text-red-500 text-sm'>
              {error.message || t('logs.loadingFailed')}
            </div>
          )}
          {logs.length === 0 && !error ? (
            <div className='flex items-center justify-center h-32 text-muted-foreground'>
              {t('logs.noMatchingRecords')}
            </div>
          ) : (
            <div>
              {logs.map((log) => (
                <LogItem key={log.id} log={log} />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
      <CardFooter>
        <TablePagination
          className='pb-0'
          total={total}
          page={page}
          pageSize={pageSize}
          onChange={handlePageChange}
        />
      </CardFooter>
    </Card>
  )
}
