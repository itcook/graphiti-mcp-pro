'use client'

import { useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useTheme } from '@/components/theme-provider'
import { useLanguage } from '@/contexts/language-context'
import { Sun, Moon, Languages, ChevronDown, PanelLeft } from 'lucide-react'

const routeMap = {
  '/': 'nav.home',
  '/settings': 'nav.settings',
  '/token-usage': 'nav.tokenUsage',
  '/logs': 'nav.logs',
}

export function Navbar(props: { style: React.CSSProperties; onToggleSidebar?: () => void }) {
  const location = useLocation()
  const { theme, setTheme } = useTheme()
  const { language, setLanguage, t } = useLanguage()

  const getBreadcrumbs = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean)
    const breadcrumbs = [{ name: t('nav.home'), path: '/' }]

    if (pathSegments.length > 0) {
      const currentPath = location.pathname
      const routeKey = routeMap[currentPath as keyof typeof routeMap]
      if (routeKey) {
        breadcrumbs.push({ name: t(routeKey), path: currentPath })
      }
    }
    return breadcrumbs
  }

  const breadcrumbs = getBreadcrumbs()
  const currentPageName = breadcrumbs[breadcrumbs.length - 1]?.name

  const toggleTheme = () => {
    if (theme === 'light') {
      setTheme('dark')
    } else {
      setTheme('light')
    }
  }

  const getThemeIcon = () => {
    if (theme === 'light') {
      return <Sun className='h-4 w-4' />
    } else if (theme === 'dark') {
      return <Moon className='h-4 w-4' />
    }
  }

  return (
    <div
      className='bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 fixed z-30'
      style={props.style}>
      <div className='flex h-14 items-center justify-between w-full px-6 pl-3 border-b'>
        <div className='flex items-center'>
          <Button variant='ghost' size='icon' onClick={props.onToggleSidebar}>
            <PanelLeft className='h-5 w-5 stroke-gray-500' />
          </Button>

          <div className='w-[1px] h-4 bg-border ml-1 mr-4' />

          {/* Breadcrumb navigation */}
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage>{currentPageName}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        {/* Right side action buttons */}
        <div className='flex items-center space-x-2 z-40'>
          {/* Theme toggle - changed to toggle mode */}
          <Button
            variant='ghost'
            size='sm'
            className='h-8 w-8 px-0 mr-2'
            onClick={toggleTheme}
            title={`Current: ${theme}`}>
            {getThemeIcon()}
            <span className='sr-only'>Toggle theme</span>
          </Button>

          {/* Language switch */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant='ghost' size='sm' className='h-8 px-2'>
                <Languages className='h-4 w-4' />
                <span className='ml-1 text-xs'>{language === 'zh-CN' ? '中' : 'EN'}</span>
                <ChevronDown className='h-3 w-3 ml-1' />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end'>
              <DropdownMenuItem
                onClick={() => setLanguage('zh-CN')}
                className={language === 'zh-CN' ? 'bg-accent' : ''}>
                <span className='mr-2'>🇨🇳</span>
                中文
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => setLanguage('en-US')}
                className={language === 'en-US' ? 'bg-accent' : ''}>
                <span className='mr-2'>🇺🇸</span>
                English
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}
