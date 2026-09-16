import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import { getToken } from './store/auth'

const ChatPage = lazy(() => import('./pages/ChatPage'))
const DataPage = lazy(() => import('./pages/DataPage'))
const GraphPage = lazy(() => import('./pages/GraphPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const KnowledgeLibraryPage = lazy(() => import('./pages/KnowledgeLibraryPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))

function PageFallback() {
  return (
    <div className="flex h-full min-h-[240px] items-center justify-center text-sm text-ink-700 dark:text-neutral-300">
      页面加载中…
    </div>
  )
}

function Protected({ children }: { children: React.ReactNode }) {
  if (!getToken()) {
    return <Navigate to='/login' replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <div className="h-full min-h-0">
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path='/login' element={<LoginPage />} />
          <Route
            path='*'
            element={
              <Protected>
                <AppLayout>
                  <Routes>
                    <Route path='/' element={<HomePage />} />
                    <Route path='/library' element={<KnowledgeLibraryPage />} />
                    <Route path='/data' element={<DataPage />} />
                    <Route path='/graph' element={<GraphPage />} />
                    <Route path='/chat' element={<ChatPage />} />
                    <Route path='/settings' element={<SettingsPage />} />
                  </Routes>
                </AppLayout>
              </Protected>
            }
          />
        </Routes>
      </Suspense>
    </div>
  )
}
