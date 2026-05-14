import { Button, Input, List, Modal, Space, Switch, Tag, Tooltip, Typography, message } from 'antd'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowUp, BookOpen, Brain, ChevronsLeft, ChevronsRight, Paperclip, Plus } from 'lucide-react'
import type { ChangeEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '../lib/utils'
import { chatStreamQuery, createChatSession, getHistory, getSessions } from '../services/api'

const CHAT_SESSION_KEY = 'pgka_chat_session_id'
const CHAT_SHOW_THINKING_KEY = 'pgka_chat_show_thinking'
const TOPICS_COLLAPSED_KEY = 'pgka_chat_topics_collapsed'
const ATTACH_MAX_CHARS = 48000

const TEXT_FILE_EXT = /\.(txt|md|markdown|csv|json|xml|log|yaml|yml)$/i

type CitationItem = {
  source?: string
  content?: string
  score?: number
  metadata?: Record<string, any>
}

type SessionRow = { session_id: string; user_id?: string; created_at?: string | null }

function loadStoredSessionId(): string {
  const saved = localStorage.getItem(CHAT_SESSION_KEY)
  if (saved) return saved
  const created = `sess-${Date.now()}`
  localStorage.setItem(CHAT_SESSION_KEY, created)
  return created
}

function formatSessionTime(iso?: string | null) {
  if (!iso) return '待开始'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return ''
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return ''
  }
}

function normalizeHistoryRows(items: any[]): any[] {
  return (items || []).map((row, idx) => {
    let citations = row.citations
    if (typeof row.citations_json === 'string' && citations == null) {
      try {
        citations = JSON.parse(row.citations_json)
      } catch {
        citations = undefined
      }
    }
    return {
      id: `db-${row.id ?? idx}`,
      role: row.role,
      content: row.content || '',
      citations,
      thinking: '',
      question: '',
    }
  })
}

export default function ChatPage() {
  const [sessionId, setSessionId] = useState(loadStoredSessionId)
  const [sessions, setSessions] = useState<SessionRow[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [creatingTopic, setCreatingTopic] = useState(false)
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<any[]>([])
  const [sending, setSending] = useState(false)
  const [showThinking, setShowThinking] = useState(() => {
    return localStorage.getItem(CHAT_SHOW_THINKING_KEY) === '1'
  })
  const [citationModalOpen, setCitationModalOpen] = useState(false)
  const [activeCitation, setActiveCitation] = useState<CitationItem | null>(null)
  const [activeQuestion, setActiveQuestion] = useState('')
  const [expandedThinkingIds, setExpandedThinkingIds] = useState<Record<string, boolean>>({})
  const [attachment, setAttachment] = useState<{ name: string; text: string } | null>(null)
  const [topicsCollapsed, setTopicsCollapsed] = useState(() => {
    try {
      return localStorage.getItem(TOPICS_COLLAPSED_KEY) === '1'
    } catch {
      return false
    }
  })
  const chatBodyRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const historyReqIdRef = useRef(0)

  const mergedSessions = useMemo(() => {
    const byId = new Map(sessions.map((s) => [s.session_id, s]))
    if (sessionId && !byId.has(sessionId)) {
      return [{ session_id: sessionId, created_at: null }, ...sessions]
    }
    return sessions
  }, [sessions, sessionId])

  const loadSessions = useCallback(async () => {
    setSessionsLoading(true)
    try {
      const data = await getSessions()
      setSessions(data.items || [])
    } catch {
      /* 未登录等 */
    } finally {
      setSessionsLoading(false)
    }
  }, [])

  const refreshMessages = useCallback(async () => {
    const rid = ++historyReqIdRef.current
    try {
      const data = await getHistory(sessionId, 250)
      if (rid !== historyReqIdRef.current) return
      const raw = data?.items
      const list = Array.isArray(raw) ? raw : []
      setMessages(normalizeHistoryRows(list))
    } catch {
      if (rid !== historyReqIdRef.current) return
      setMessages([])
    }
  }, [sessionId])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  useEffect(() => {
    localStorage.setItem(CHAT_SESSION_KEY, sessionId)
  }, [sessionId])

  useEffect(() => {
    refreshMessages()
  }, [refreshMessages])

  useEffect(() => {
    localStorage.setItem(CHAT_SHOW_THINKING_KEY, showThinking ? '1' : '0')
  }, [showThinking])

  useEffect(() => {
    try {
      localStorage.setItem(TOPICS_COLLAPSED_KEY, topicsCollapsed ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [topicsCollapsed])

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight
    }
  }, [messages])

  const queryKeywords = useMemo(() => {
    return activeQuestion
      .toLowerCase()
      .split(/[\s，。！？、,.!?;；:：]+/)
      .map((x) => x.trim())
      .filter((x) => x.length >= 2)
      .slice(0, 8)
  }, [activeQuestion])

  function renderHighlighted(text: string, keywords: string[]) {
    if (!text) return null
    if (!keywords.length) return <>{text}</>
    const escaped = keywords.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    const pattern = new RegExp(`(${escaped.join('|')})`, 'ig')
    const parts = text.split(pattern)
    return (
      <>
        {parts.map((part, idx) => {
          const hit = keywords.some((k) => part.toLowerCase() === k.toLowerCase())
          return hit ? (
            <mark
              key={`${part}-${idx}`}
              className="rounded px-0.5"
              style={{ background: 'oklch(0.93 0.08 95)' }}
            >
              {part}
            </mark>
          ) : (
            <span key={`${part}-${idx}`}>{part}</span>
          )
        })}
      </>
    )
  }

  function selectSession(id: string) {
    if (id === sessionId || sending) return
    setSessionId(id)
    setAttachment(null)
    setQuery('')
    setExpandedThinkingIds({})
  }

  async function newTopic() {
    if (creatingTopic) return
    setCreatingTopic(true)
    try {
      const { session_id } = await createChatSession()
      setSessionId(session_id)
      setMessages([])
      setQuery('')
      setAttachment(null)
      await loadSessions()
      message.success('已新建话题')
    } catch {
      message.error('新建话题失败')
    } finally {
      setCreatingTopic(false)
    }
  }

  async function send() {
    if (!query.trim() && !attachment) return
    const text = query.trim() || '（见附件内容）'
    const attachText = attachment?.text ?? null
    const userDisplay =
      attachment && query.trim()
        ? `${text}\n\n📎 附件：${attachment.name}`
        : attachment
          ? `📎 附件：${attachment.name}\n\n${text}`
          : text
    const assistantId = `assistant-${Date.now()}`

    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: 'user', content: userDisplay },
      { id: assistantId, role: 'assistant', question: text, content: '', thinking: '', citations: [] },
    ])
    setExpandedThinkingIds((prev) => ({ ...prev, [assistantId]: false }))
    setQuery('')
    setAttachment(null)
    setSending(true)

    try {
      await chatStreamQuery(query.trim() || '请根据附件内容回答。', sessionId, showThinking, (event) => {
        if (event.type === 'delta') {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: `${m.content || ''}${event.content || ''}` } : m))
          )
        }
        if (event.type === 'thinking' || event.type === 'thinking_delta') {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, thinking: `${m.thinking || ''}${event.content || ''}` } : m))
          )
        }
        if (event.type === 'done') {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, citations: event.citations || [] } : m))
          )
        }
      }, attachText)
    } finally {
      setSending(false)
      void loadSessions()
    }
  }

  function onPickFile() {
    fileInputRef.current?.click()
  }

  async function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    if (!TEXT_FILE_EXT.test(file.name) && !file.type.startsWith('text/')) {
      message.warning('当前仅支持文本类文件（如 .txt / .md / .csv / .json），其它格式请先转为文本')
      return
    }
    try {
      const raw = await file.text()
      const cut = raw.length > ATTACH_MAX_CHARS ? raw.slice(0, ATTACH_MAX_CHARS) : raw
      if (raw.length > ATTACH_MAX_CHARS) {
        message.info(`附件较长，已截取前 ${ATTACH_MAX_CHARS} 字符参与对话`)
      }
      setAttachment({ name: file.name, text: cut })
    } catch {
      message.error('无法读取该文件')
    }
  }

  function toggleThinking(messageId: string) {
    setExpandedThinkingIds((prev) => ({ ...prev, [messageId]: !prev[messageId] }))
  }

  function openCitation(citation: CitationItem, question: string) {
    setActiveCitation(citation)
    setActiveQuestion(question)
    setCitationModalOpen(true)
  }

  function expandTopics() {
    setTopicsCollapsed(false)
    void loadSessions()
  }

  return (
    <div className="flex h-full min-h-0 flex-col bg-gradient-to-b from-white/90 via-surface-50/90 to-surface-100 md:flex-row dark:from-zinc-950/90 dark:via-zinc-900/80 dark:to-zinc-950">
      {!topicsCollapsed ? (
        <aside className="flex max-h-[36vh] shrink-0 flex-col border-b border-neutral-200/70 dark:border-white/10 md:max-h-none md:w-[220px] md:border-b-0 md:border-r">
          <div className="flex shrink-0 items-center justify-between border-b border-neutral-200/60 px-3 py-2.5 dark:border-white/10">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-700/80 dark:text-neutral-400">
              话题
            </span>
            <Tooltip title="收起话题栏，扩大对话区">
              <Button
                type="text"
                size="small"
                className="!flex !items-center !gap-0.5 !text-xs !text-ink-700 dark:!text-neutral-300"
                onClick={() => setTopicsCollapsed(true)}
                aria-label="收起话题栏"
              >
                <ChevronsLeft className="h-3.5 w-3.5" aria-hidden />
                收起
              </Button>
            </Tooltip>
          </div>
          <div className="min-h-0 flex-1 space-y-1 overflow-y-auto p-2 [scrollbar-gutter:stable]">
            {mergedSessions.map((s) => {
              const active = s.session_id === sessionId
              return (
                <button
                  key={s.session_id}
                  type="button"
                  disabled={sending}
                  onClick={() => selectSession(s.session_id)}
                  className={cn(
                    'flex w-full flex-col rounded-xl px-3 py-2.5 text-left text-[13px] transition-colors',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50',
                    active
                      ? 'bg-brand-600 text-white shadow-md shadow-brand-600/20 dark:bg-brand-600'
                      : 'bg-white/80 text-ink-900 hover:bg-neutral-100 dark:bg-white/5 dark:text-neutral-200 dark:hover:bg-white/10'
                  )}
                >
                  <span className="truncate font-medium leading-snug">
                    {formatSessionTime(s.created_at)}
                    <span className={cn('opacity-80', active ? 'text-white/90' : 'text-ink-700/70 dark:text-neutral-400')}>
                      {' '}
                      · …{s.session_id.slice(-6)}
                    </span>
                  </span>
                  <span
                    className={cn(
                      'mt-0.5 truncate text-[11px]',
                      active ? 'text-white/75' : 'text-ink-700/55 dark:text-neutral-500'
                    )}
                  >
                    {s.created_at ? '已建档' : '本地 / 待同步'}
                  </span>
                </button>
              )
            })}
            {!mergedSessions.length && !sessionsLoading ? (
              <p className="px-2 py-4 text-center text-xs text-neutral-500">暂无话题，点击右上方 + 新建</p>
            ) : null}
          </div>
        </aside>
      ) : (
        <Tooltip title="展开话题栏">
          <button
            type="button"
            onClick={expandTopics}
            className={cn(
              'flex w-11 shrink-0 flex-col items-center justify-center gap-1 border-b border-neutral-200/70 py-3 md:border-b-0 md:border-r dark:border-white/10',
              'bg-white/50 text-ink-700 transition-colors hover:bg-neutral-100 dark:bg-zinc-900/50 dark:text-neutral-200 dark:hover:bg-white/10'
            )}
            aria-label="展开话题栏"
          >
            <ChevronsRight className="h-5 w-5" strokeWidth={2} aria-hidden />
            <span className="hidden text-[10px] font-medium md:block" style={{ writingMode: 'vertical-rl' }}>
              话题
            </span>
          </button>
        </Tooltip>
      )}

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-neutral-200/70 px-4 py-3 md:px-6 dark:border-white/10">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              {topicsCollapsed ? (
                <Button type="link" size="small" className="!px-1 !text-brand-700 dark:!text-brand-400" onClick={expandTopics}>
                  话题
                </Button>
              ) : null}
              <Typography.Text strong className="!text-[15px] !text-ink-900 dark:!text-neutral-100">
                对话
              </Typography.Text>
              <Tag className="!m-0 !rounded-lg !border-neutral-200/80 !bg-white/80 !text-xs !font-normal !text-ink-700 dark:!border-white/15 dark:!bg-white/10 dark:!text-neutral-300">
                当前 …{sessionId.slice(-8)}
              </Tag>
            </div>
            <p className="mt-0.5 text-xs text-ink-700/75 dark:text-neutral-400">RAG 检索 · 流式输出 · 引用可追溯</p>
          </div>
          <Tooltip title="新建话题">
            <Button
              type="primary"
              shape="circle"
              size="large"
              loading={creatingTopic}
              disabled={sending}
              className="!flex !h-11 !w-11 !shrink-0 !items-center !justify-center !shadow-md !shadow-brand-600/25"
              icon={<Plus className="h-5 w-5" strokeWidth={2.4} />}
              onClick={() => void newTopic()}
              aria-label="新建话题"
            />
          </Tooltip>
        </div>

        <div
          ref={chatBodyRef}
          className="min-h-0 flex-1 overflow-y-auto scroll-smooth [scrollbar-gutter:stable]"
        >
          <div className="mx-auto w-full max-w-3xl px-4 py-6 md:px-6">
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                className="mx-auto mt-8 max-w-lg text-center"
              >
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500/15 to-brand-600/10 ring-1 ring-brand-500/20">
                  <MessageGlyph className="h-7 w-7 text-brand-600" />
                </div>
                <h2 className="font-display text-2xl font-semibold tracking-tight text-ink-900 md:text-3xl dark:text-neutral-100">
                  今天想了解哪一段电网知识？
                </h2>
                <p className="mt-2 text-[15px] leading-relaxed text-ink-700 dark:text-neutral-400">
                  输入设备、间隔、规程或故障场景，智能体将结合知识库与图谱给出可引用回答。
                </p>
              </motion.div>
            )}

            <List className="!border-none">
              <AnimatePresence initial={false}>
                {messages.map((item: any) => (
                  <List.Item key={item.id} className="!border-none !px-0 !py-2">
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.2, ease: 'easeOut' }}
                      className={cn(
                        'flex w-full',
                        item.role === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      <div
                        className={cn(
                          'max-w-[min(100%,34rem)] rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-sm ring-1 transition-shadow duration-200',
                          item.role === 'user'
                            ? 'bg-gradient-to-br from-brand-600 to-brand-500 text-white ring-black/5'
                            : 'bg-white/90 text-ink-900 ring-neutral-200/80 backdrop-blur-sm dark:bg-zinc-900/85 dark:text-neutral-100 dark:ring-white/10'
                        )}
                      >
                        <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide opacity-90">
                          {item.role === 'user' ? '你' : '智能体'}
                        </div>

                        {showThinking && item.role === 'assistant' && item.thinking ? (
                          <div className="mb-2">
                            <Button
                              size="small"
                              type="text"
                              className="!h-8 !rounded-lg !px-2 !text-ink-700 hover:!bg-neutral-100 dark:!text-neutral-300 dark:hover:!bg-white/10"
                              onClick={() => toggleThinking(item.id)}
                            >
                              {expandedThinkingIds[item.id] ? '折叠推理' : '展开推理'}
                            </Button>
                            {expandedThinkingIds[item.id] ? (
                              <div className="mt-2 rounded-xl border border-dashed border-neutral-300/80 bg-surface-50/80 px-3 py-2 text-[13px] text-ink-700 dark:border-white/15 dark:bg-zinc-950/50 dark:text-neutral-300">
                                <Typography.Paragraph className="!mb-0 !whitespace-pre-wrap">
                                  {item.thinking}
                                </Typography.Paragraph>
                              </div>
                            ) : null}
                          </div>
                        ) : null}

                        <Typography.Paragraph
                          className={cn(
                            '!mb-0 !whitespace-pre-wrap',
                            item.role === 'user' && '!text-white/95'
                          )}
                        >
                          {item.content}
                        </Typography.Paragraph>

                        {item.role === 'assistant' && item.citations?.length ? (
                          <div className="mt-3 border-t border-neutral-200/70 pt-3 dark:border-white/10">
                            <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-ink-700 dark:text-neutral-300">
                              <BookOpen className="h-3.5 w-3.5" aria-hidden />
                              引用
                            </div>
                            <Space wrap size={[8, 8]}>
                              {item.citations.map((c: any, idx: number) => {
                                const source = c.source || c.metadata?.file_name || `来源${idx + 1}`
                                return (
                                  <Tag
                                    key={`${source}-${idx}`}
                                    className="!m-0 !cursor-pointer !rounded-lg !border-brand-500/25 !bg-brand-500/10 !px-2.5 !py-0.5 !text-brand-950 hover:!border-brand-500/40 dark:!text-brand-200"
                                    onClick={() => openCitation(c, item.question || '')}
                                  >
                                    {source}
                                  </Tag>
                                )
                              })}
                            </Space>
                          </div>
                        ) : null}
                      </div>
                    </motion.div>
                  </List.Item>
                ))}
              </AnimatePresence>
            </List>
          </div>
        </div>

        <div className="shrink-0 border-t border-neutral-200/80 bg-white/70 px-4 py-4 backdrop-blur-xl supports-[backdrop-filter]:bg-white/55 md:px-6 dark:border-white/10 dark:bg-zinc-950/60">
          <div className="mx-auto w-full max-w-3xl">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".txt,.md,.markdown,.csv,.json,.xml,.log,.yaml,.yml,text/plain,text/csv,text/markdown"
              onChange={onFileChange}
            />
            <div className="relative rounded-[1.35rem] border border-neutral-200/90 bg-white/95 p-2 shadow-[0_12px_48px_-24px_rgba(15,23,42,0.35)] ring-1 ring-black/[0.03] dark:border-white/12 dark:bg-zinc-900/80">
              {attachment ? (
                <div className="mb-1 flex items-center gap-2 px-2 pt-1">
                  <Tag
                    closable
                    onClose={() => setAttachment(null)}
                    className="!m-0 !rounded-lg !border-brand-500/30 !bg-brand-500/10 !text-xs !text-brand-950 dark:!text-brand-200"
                  >
                    {attachment.name}
                  </Tag>
                  <span className="text-[11px] text-ink-700/65 dark:text-neutral-500">将随本次提问一并发送</span>
                </div>
              ) : null}
              <Input.TextArea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault()
                    void send()
                  }
                }}
                rows={3}
                placeholder="向智能体提问…（Shift+Enter 换行）"
                className="!min-h-[88px] !resize-none !border-none !bg-transparent !px-3 !py-2 !text-[15px] !shadow-none focus:!shadow-none dark:!text-neutral-100"
              />
              <div className="flex flex-col gap-3 px-2 pb-1 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={onPickFile}
                    className={cn(
                      'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-neutral-200/90 bg-white text-ink-700 transition-colors',
                      'hover:border-brand-500/40 hover:bg-brand-500/5 hover:text-brand-700',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50',
                      'dark:border-white/12 dark:bg-white/5 dark:text-neutral-300 dark:hover:bg-white/10'
                    )}
                    title="附加文本文件"
                    aria-label="附加文本文件"
                  >
                    <Paperclip className="h-[18px] w-[18px]" strokeWidth={2.2} aria-hidden />
                  </button>
                  <div className="flex items-center gap-2 rounded-full border border-neutral-200/80 bg-neutral-50/90 px-3 py-1.5 text-xs text-ink-700 shadow-sm dark:border-white/12 dark:bg-white/5 dark:text-neutral-300">
                    <Brain className="h-3.5 w-3.5 shrink-0 text-brand-600 dark:text-brand-400" aria-hidden />
                    <span className="whitespace-nowrap">思考过程</span>
                    <Switch checked={showThinking} onChange={setShowThinking} size="small" />
                  </div>
                </div>
                <Button
                  type="primary"
                  onClick={() => void send()}
                  loading={sending}
                  disabled={!query.trim() && !attachment}
                  className="!flex !h-10 !min-w-[40px] !items-center !justify-center !self-end !rounded-xl !border-none !px-4 !shadow-md !shadow-brand-600/20 sm:!self-auto"
                  icon={!sending ? <ArrowUp className="h-4 w-4" strokeWidth={2.5} /> : undefined}
                >
                  {sending ? '发送中' : '发送'}
                </Button>
              </div>
            </div>
            <p className="mt-2 text-center text-[11px] text-ink-700/60 dark:text-neutral-500">
              回答由大模型与本地知识库生成，请以现场规程与调度指令为准。
            </p>
          </div>
        </div>
      </div>

      <Modal
        title={activeCitation?.source || activeCitation?.metadata?.file_name || '引用详情'}
        open={citationModalOpen}
        onCancel={() => setCitationModalOpen(false)}
        footer={null}
        width={820}
        classNames={{ body: '!pt-2' }}
      >
        <Space direction="vertical" className="w-full" size="middle">
          <Tag className="!m-0 !rounded-lg !border-purple-200 !bg-purple-50 !text-purple-900 dark:!border-purple-500/30 dark:!bg-purple-950/40 dark:!text-purple-200">
            问题关键词高亮
          </Tag>
          <Typography.Paragraph className="!mb-0 !whitespace-pre-wrap !leading-relaxed">
            {renderHighlighted(activeCitation?.content || '暂无片段内容', queryKeywords)}
          </Typography.Paragraph>
        </Space>
      </Modal>
    </div>
  )
}

function MessageGlyph({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 4C8.5 4 5.5 6.2 5.5 9c0 1.6.8 3 2 4l-.8 3.2 3.4-1.4c.6.2 1.2.2 1.9.2 3.5 0 6.5-2.2 6.5-5 0-2.8-3-5-6.5-5Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <circle cx="9" cy="9" r="1" fill="currentColor" />
      <circle cx="12.5" cy="9" r="1" fill="currentColor" />
      <circle cx="16" cy="9" r="1" fill="currentColor" />
    </svg>
  )
}
