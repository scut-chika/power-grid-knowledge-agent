import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { BrowserRouter } from 'react-router-dom'
import { useAntdTheme } from '../context/ThemeContext'
import App from '../App'

export default function AppRoot() {
  const antdTheme = useAntdTheme()
  return (
    <ConfigProvider locale={zhCN} theme={antdTheme}>
      <BrowserRouter>
        <div className="h-full min-h-0">
          <App />
        </div>
      </BrowserRouter>
    </ConfigProvider>
  )
}
