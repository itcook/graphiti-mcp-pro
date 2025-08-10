'use client'

import type React from 'react'

import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Monitor, FileText, ChartColumnStacked, Settings2 } from 'lucide-react'
import { Navbar } from './navbar'
import { useLanguage } from '@/contexts/language-context'

const navigation = [
  { name: 'nav.home', href: '/', icon: Monitor },
  { name: 'nav.settings', href: '/settings', icon: Settings2 },
  { name: 'nav.tokenUsage', href: '/token-usage', icon: ChartColumnStacked },
  { name: 'nav.logs', href: '/logs', icon: FileText },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const { t } = useLanguage()

  const navbarWidthStyle = {
    width: sidebarCollapsed ? 'calc(100% - 4rem)' : 'calc(100% - 16rem)',
  }

  function handleCollapseByWindowWidth() {
    const width = window.innerWidth
    if (width <= 1280) {
      setSidebarCollapsed(true)
    } else {
      setSidebarCollapsed(false)
    }
  }

  useEffect(() => {
    handleCollapseByWindowWidth()

    window.addEventListener('resize', handleCollapseByWindowWidth)
    handleCollapseByWindowWidth()
    return () => {
      window.removeEventListener('resize', handleCollapseByWindowWidth)
    }
  }, [window.innerWidth])

  const Sidebar = ({ className }: { className?: string; isMobile?: boolean }) => (
    <div
      className={cn(
        'flex h-full flex-col fixed border-r',
        sidebarCollapsed ? 'w-16' : 'w-64',
        className
      )}>
      <div className='flex h-14 items-center justify-center border-b'>
        <div className='flex items-center'>
          <img src='/graphiti-logo.png' alt='Logo' className='h-8 w-8 rounded' />
          {!sidebarCollapsed && <span className='ml-2 font-semibold'>Graphiti MCP Pro</span>}
        </div>
      </div>
      <ScrollArea className='flex-1 px-3 py-4'>
        <nav className='space-y-2'>
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                // onClick={() => setSidebarCollapsed(true)}
                className={cn(
                  'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
                title={sidebarCollapsed ? t(item.name) : undefined}>
                <item.icon className='h-4 w-4' />
                {!sidebarCollapsed && <span className='ml-3'>{t(item.name)}</span>}
              </Link>
            )
          })}
        </nav>
      </ScrollArea>
    </div>
  )

  return (
    <div className='flex h-screen bg-background'>
      <div
        className={cn('bg-card transition-all duration-300', sidebarCollapsed ? 'w-16' : 'w-64')}>
        <Sidebar />
      </div>

      {!sidebarCollapsed && (
        <div className='fixed inset-0 z-50 lg:hidden'>
          {/* Backdrop */}
          <div className='fixed inset-0 bg-black/50' />

          {/* Sidebar */}
          <div className='fixed left-0 top-0 h-full w-64 bg-card border-r'>
            <Sidebar isMobile />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className='flex-1 flex flex-col'>
        {/* Top Navbar */}
        <Navbar
          style={navbarWidthStyle}
          onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main Content Area */}
        <main className='flex-1 p-6 pt-20'>{children}</main>
      </div>
    </div>
  )
}
