'use client'
import { lazy, Suspense } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useLanguage } from '@/contexts/language-context'
import { Card, CardContent } from '@/components/ui/card'
import { LoaderIcon } from 'lucide-react'

function LoadingCard() {
  return (
    <Card className='h-full'>
      <CardContent className='h-full flex items-center justify-center'>
        <LoaderIcon className='size-4 animate-spin stroke-gray-400' />
      </CardContent>
    </Card>
  )
}

const RealtimeLogsTabContent = lazy(() => import('./RealtimeLogsTabContent'))
const HistoryLogsTabContent = lazy(() => import('./HistoryLogsTabContent'))

export function Logs() {
  const { t } = useLanguage()

  return (
    <div className='space-y-6 h-[calc(100%-3rem)]'>
      <Tabs defaultValue='realtime' className='space-y-4 h-full'>
        <TabsList>
          <TabsTrigger value='realtime'>{t('logs.realtime')}</TabsTrigger>
          <TabsTrigger value='history'>{t('logs.history')}</TabsTrigger>
        </TabsList>

        <TabsContent value='realtime' className='h-full'>
          <Suspense fallback={<LoadingCard />}>
            <RealtimeLogsTabContent />
          </Suspense>
        </TabsContent>

        <TabsContent value='history' className='h-full'>
          <Suspense fallback={<LoadingCard />}>
            <HistoryLogsTabContent />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  )
}
