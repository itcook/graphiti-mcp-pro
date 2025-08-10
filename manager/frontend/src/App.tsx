import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@/components/theme-provider'
import { LanguageProvider } from '@/contexts/language-context'
import { Toaster } from '@/components/ui/sonner'
import { Layout } from './components/layout'
import { Home } from './pages/home'
import { Settings } from './pages/settings'
import { TokenUsage } from './pages/token-usage'
import { Logs } from './pages/logs'

export default function App() {
  return (
    <ThemeProvider defaultTheme='dark' storageKey='mcp-dashboard-theme'>
      <LanguageProvider>
        <Router future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
          <Layout>
            <Routes>
              <Route path='/' element={<Home />} />
              <Route path='/settings' element={<Settings />} />
              <Route path='/token-usage' element={<TokenUsage />} />
              <Route path='/logs' element={<Logs />} />
            </Routes>
          </Layout>
          <Toaster />
        </Router>
      </LanguageProvider>
    </ThemeProvider>
  )
}
