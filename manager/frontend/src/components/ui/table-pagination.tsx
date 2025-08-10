import * as React from 'react'
import {
  Pagination,
  PaginationContent,
  PaginationLink,
  PaginationItem,
  PaginationEllipsis,
} from '@/components/ui/pagination'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useLanguage } from '@/contexts/language-context'
import { ChevronLeftIcon, ChevronRightIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type PageListItem = number | '...'

export function TablePagination(props: {
  total: number
  page: number
  pageSize: number
  onChange?: ({ page, pageSize }: { page: number; pageSize: number }) => void
  className?: string
}) {
  const { t } = useLanguage()
  const { total, page, pageSize, onChange } = props
  const [currentPage, setCurrentPage] = React.useState(page)
  const [currentPageSize, setCurrentPageSize] = React.useState(
    [10, 20, 50, 100].includes(pageSize) ? pageSize : 20
  )
  const [totalPages, setTotalPages] = React.useState(0)

  React.useEffect(() => {
    setTotalPages(Math.ceil(total / currentPageSize))
  }, [total, currentPageSize])

  const [pageList, setPageList] = React.useState<PageListItem[]>([])

  React.useEffect(() => {
    const maxVisiblePages = 5

    if (totalPages <= maxVisiblePages) {
      setPageList(Array.from({ length: totalPages }, (_, i) => i + 1))
    } else {
      const _pageList: PageListItem[] = [1]

      if (currentPage > 3) {
        _pageList.push('...')
      }

      const startPage = Math.max(2, currentPage - 1)
      const endPage = Math.min(totalPages - 1, currentPage + 1)

      for (let i = startPage; i <= endPage; i++) {
        _pageList.push(i)
      }

      if (currentPage < totalPages - 2) {
        _pageList.push('...')
      }

      _pageList.push(totalPages)

      setPageList(_pageList)
    }
  }, [totalPages, currentPage])

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage)
    onChange?.({ page: newPage, pageSize })
  }
  const handlePageSizeChange = (newPageSize: number) => {
    setCurrentPageSize(newPageSize)
    setCurrentPage(1)
    onChange?.({ page: 1, pageSize: newPageSize })
  }
  return (
    <div className={cn('flex items-center justify-between w-full py-4', props.className)}>
      <div className='flex items-center space-x-2'>
        <Select
          value={currentPageSize.toString()}
          onValueChange={(value) => handlePageSizeChange(Number(value))}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='10'>10 / {t('tokenUsage.record.page')}</SelectItem>
            <SelectItem value='20'>20 / {t('tokenUsage.record.page')}</SelectItem>
            <SelectItem value='50'>50 / {t('tokenUsage.record.page')}</SelectItem>
            <SelectItem value='100'>100 / {t('tokenUsage.record.page')}</SelectItem>
          </SelectContent>
        </Select>
        {totalPages > 1 && (
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationLink
                  onClick={() => handlePageChange(currentPage - 1)}
                  isActive={false}
                  disabled={currentPage === 1}
                  size='default'
                  aria-label='Go to previous page'>
                  <ChevronLeftIcon />
                </PaginationLink>
              </PaginationItem>
              {pageList.map((item, index) => {
                if (item === '...') {
                  return (
                    <PaginationItem key={index}>
                      <PaginationEllipsis />
                    </PaginationItem>
                  )
                }
                return (
                  <PaginationItem key={index}>
                    <PaginationLink
                      onClick={() => handlePageChange(item)}
                      isActive={currentPage === item}
                      disabled={currentPage === item}>
                      {item}
                    </PaginationLink>
                  </PaginationItem>
                )
              })}
              <PaginationItem>
                <PaginationLink
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  size='default'
                  aria-label='Go to next page'>
                  <ChevronRightIcon />
                </PaginationLink>
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>
      <div className='text-sm text-muted-foreground'>
        {t('tokenUsage.record.total')} {total}{' '}
        {total === 1 ? t('tokenUsage.record.item') : t('tokenUsage.record.items')}
      </div>
    </div>
  )
}
