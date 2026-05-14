import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import ChatPage from './pages/ChatPage'
import DataPage from './pages/DataPage'
import GraphPage from './pages/GraphPage'
import HomePage from './pages/HomePage'
import KnowledgeLibraryPage from './pages/KnowledgeLibraryPage'
import LoginPage from './pages/LoginPage'
import SettingsPage from './pages/SettingsPage'
import { getToken } from './store/auth'

function Protected({ children }: { children: React.ReactNode }) {
  if (!getToken()) {
    return <Navigate to='/login' replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <div className="h-full min-h-0">
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
    </div>
  )
}
