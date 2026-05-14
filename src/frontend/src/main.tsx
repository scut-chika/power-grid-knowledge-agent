import React from 'react'
import ReactDOM from 'react-dom/client'
import 'antd/dist/reset.css'
import AppRoot from './components/AppRoot'
import { ThemeProvider } from './context/ThemeContext'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AppRoot />
    </ThemeProvider>
  </React.StrictMode>
)
