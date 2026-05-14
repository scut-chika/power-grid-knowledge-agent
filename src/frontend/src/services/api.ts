import http from './http'
import { clearAuth, getToken } from '../store/auth'

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL
  if (raw !== undefined && raw !== null && String(raw).trim() !== '') {
    return String(raw).replace(/\/$/, '')
  }
  return ''
}

export async function login(username: string, password: string) {
  const res = await http.post('/api/auth/login', { username, password })
  return res.data.data
}

export async function getSystemStatus() {
  const res = await http.get('/api/system/status')
  return res.data.data
}

export async function getFiles(params: Record<string, any>) {
  const res = await http.get('/api/data/list', { params })
  return res.data.data
}

export async function uploadFiles(files: File[], fileType: string) {
  const form = new FormData()
  for (const f of files) {
    form.append('files', f)
  }
  const res = await http.post(
    `/api/data/upload?file_type=${encodeURIComponent(fileType)}`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return res.data.data
}

export async function buildKnowledge(build_type: 'incremental' | 'full') {
  const res = await http.post('/api/knowledge/build', { build_type })
  return res.data.data
}

export async function getBuildStatus(task_id: string) {
  const res = await http.get('/api/knowledge/status', { params: { task_id } })
  return res.data.data
}

export async function getGraph() {
  const res = await http.get('/api/knowledge/graph')
  return res.data.data
}

export async function chatQuery(query: string, session_id: string) {
  const res = await http.post('/api/chat/query', { query, session_id })
  return res.data.data
}

export async function chatStreamQuery(
  query: string,
  session_id: string,
  showThinking: boolean,
  onEvent: (event: any) => void,
  attachmentText?: string | null
) {
  const token = getToken()
  if (!token) {
    clearAuth()
    if (!window.location.pathname.startsWith('/login')) {
      window.location.assign('/login')
    }
    throw new Error('请先登录后再使用对话')
  }

  const url = `${apiBase()}/api/chat/stream`
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      query,
      session_id,
      show_thinking: showThinking,
      attachment_text: attachmentText?.trim() ? attachmentText.trim() : null,
    }),
  })

  if (response.status === 401) {
    clearAuth()
    if (!window.location.pathname.startsWith('/login')) {
      window.location.assign('/login')
    }
    throw new Error('登录已失效（例如修改过 SECRET_KEY），请重新登录')
  }

  if (!response.ok || !response.body) {
    throw new Error('流式请求失败')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''

    for (const chunk of chunks) {
      const line = chunk.trim()
      if (!line.startsWith('data:')) continue
      const payload = line.slice(5).trim()
      if (!payload) continue
      try {
        onEvent(JSON.parse(payload))
      } catch {
        // ignore parse error for malformed chunk
      }
    }
  }
}

export async function getSessions() {
  const res = await http.get('/api/chat/session')
  return res.data.data
}

export async function createChatSession() {
  const res = await http.post('/api/chat/session')
  return res.data.data as { session_id: string }
}

export async function getHistory(session_id: string, page_size = 200) {
  const res = await http.get('/api/chat/history', {
    params: { session_id, page: 1, page_size },
  })
  return res.data.data
}

export async function getConfig() {
  const res = await http.get('/api/system/config')
  return res.data.data
}

export async function updateConfig(items: Record<string, string>) {
  const res = await http.post('/api/system/config', { items })
  return res.data as { code: number; message: string; data: Record<string, string> }
}
