import axios from 'axios'
import { clearAuth, getToken } from '../store/auth'

/** 未设置 VITE_API_BASE_URL 时使用相对路径 /api，由 Vite dev proxy 转发到后端（同源带 Cookie/鉴权更稳） */
function resolveBaseURL(): string {
  const raw = import.meta.env.VITE_API_BASE_URL
  if (raw !== undefined && raw !== null && String(raw).trim() !== '') {
    return String(raw).replace(/\/$/, '')
  }
  return ''
}

const http = axios.create({
  baseURL: resolveBaseURL(),
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status
    const url: string = err.config?.url ?? ''
    if (status === 401 && !url.includes('/auth/login')) {
      clearAuth()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.assign('/login')
      }
    }
    return Promise.reject(err)
  }
)

export default http
