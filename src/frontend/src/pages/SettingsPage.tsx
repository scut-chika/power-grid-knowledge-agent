import { Button, Card, Divider, Form, Input, message } from 'antd'
import { motion } from 'framer-motion'
import { Brain, Layers, Search, SlidersHorizontal, Sparkles } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { getConfig, updateConfig } from '../services/api'
import { cn } from '../lib/utils'

const sections = [
  { id: 'section-llm', label: '大语言模型', icon: Sparkles },
  { id: 'section-emb', label: '向量嵌入', icon: Layers },
  { id: 'section-rerank', label: '重排序', icon: Brain },
  { id: 'section-retrieve', label: '检索参数', icon: Search },
] as const

function toItems(values: Record<string, unknown>): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(values)) {
    out[k] = v === undefined || v === null ? '' : String(v)
  }
  return out
}

export default function SettingsPage() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    getConfig()
      .then((data) => {
        if (data && typeof data === 'object') {
          form.setFieldsValue(data)
        }
      })
      .catch(() => message.error('加载配置失败，请确认已登录且具备管理员权限'))
      .finally(() => setLoading(false))
  }, [form])

  useEffect(() => {
    load()
  }, [load])

  function scrollToSection(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function onSave(values: Record<string, unknown>) {
    const items = toItems(values)
    setSaving(true)
    try {
      const res = await updateConfig(items)
      if (res.code !== 0) {
        message.error(res.message || '保存失败')
        return
      }
      if (res.message && res.message !== 'ok') {
        message.warning(res.message)
      } else {
        message.success('已保存到数据库并同步 .env')
      }
      form.setFieldsValue(res.data)
    } catch {
      message.error('保存失败，请检查网络与后端服务')
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex h-full min-h-0 flex-1 flex-col overflow-hidden"
    >
      <Card
        className="settings-card-shell !mb-0 border-neutral-200/80 dark:border-white/10 dark:!bg-zinc-900/40"
        classNames={{ body: '!p-0' }}
        title={
          <span className="inline-flex items-center gap-2 font-display text-[15px] font-semibold">
            <SlidersHorizontal className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
            系统设置
          </span>
        }
      >
        <div className="flex min-h-0 flex-1 gap-0 overflow-hidden md:gap-5">
          <aside
            className="hidden w-[200px] shrink-0 flex-col self-stretch border-r border-neutral-200/80 bg-white/30 py-4 pl-1 pr-3 dark:border-white/10 dark:bg-white/[0.03] md:flex"
            aria-label="配置分区"
          >
            <div className="flex h-full flex-col space-y-1">
              <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
                分区
              </p>
              {sections.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => scrollToSection(id)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors',
                    'text-neutral-600 hover:bg-black/[0.04] dark:text-neutral-300 dark:hover:bg-white/[0.06]',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50'
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0 text-brand-600 dark:text-brand-400" aria-hidden />
                  {label}
                </button>
              ))}
            </div>
          </aside>

          <div
            className="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-y-contain rounded-xl border border-neutral-200/60 bg-white/70 px-4 py-5 shadow-[var(--shadow-glass)] dark:border-white/10 dark:bg-zinc-900/35 md:px-5 md:py-6"
            role="region"
            aria-label="配置表单"
          >
            <p className="mb-5 text-sm text-neutral-600 dark:text-neutral-400">
              默认值来自服务端环境变量；保存后将写入数据库并更新项目根目录 <code className="rounded bg-black/[0.06] px-1.5 py-0.5 text-xs dark:bg-white/10">.env</code>。
            </p>
            <Form
              form={form}
              layout="vertical"
              onFinish={onSave}
              disabled={loading}
              className="max-w-2xl"
            >
              <div id="section-llm" className="scroll-mt-4">
                <Divider orientation="left" className="!mt-0 dark:border-white/10">
                  <span className="flex items-center gap-2 text-ink-900 dark:text-neutral-100">
                    <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
                    大语言模型
                  </span>
                </Divider>
                <Form.Item name="llm_api_base_url" label="LLM API Base URL">
                  <Input placeholder="https://..." autoComplete="off" />
                </Form.Item>
                <Form.Item name="llm_api_key" label="LLM API Key">
                  <Input.Password autoComplete="off" />
                </Form.Item>
                <Form.Item name="llm_model_name" label="LLM Model Name">
                  <Input autoComplete="off" />
                </Form.Item>
              </div>

              <div id="section-emb" className="scroll-mt-4">
                <Divider orientation="left" className="dark:border-white/10">
                  <span className="flex items-center gap-2 text-ink-900 dark:text-neutral-100">
                    <Layers className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
                    向量嵌入
                  </span>
                </Divider>
                <Form.Item name="embedding_api_base_url" label="Embedding API Base URL">
                  <Input autoComplete="off" />
                </Form.Item>
                <Form.Item name="embedding_api_key" label="Embedding API Key">
                  <Input.Password autoComplete="off" />
                </Form.Item>
                <Form.Item name="embedding_model_name" label="Embedding Model Name">
                  <Input autoComplete="off" />
                </Form.Item>
              </div>

              <div id="section-rerank" className="scroll-mt-4">
                <Divider orientation="left" className="dark:border-white/10">
                  <span className="flex items-center gap-2 text-ink-900 dark:text-neutral-100">
                    <Brain className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
                    重排序
                  </span>
                </Divider>
                <Form.Item name="reranker_api_base_url" label="Reranker API Base URL">
                  <Input autoComplete="off" />
                </Form.Item>
                <Form.Item name="reranker_api_key" label="Reranker API Key">
                  <Input.Password autoComplete="off" />
                </Form.Item>
                <Form.Item name="reranker_model_name" label="Reranker Model Name">
                  <Input autoComplete="off" />
                </Form.Item>
              </div>

              <div id="section-retrieve" className="scroll-mt-4">
                <Divider orientation="left" className="dark:border-white/10">
                  <span className="flex items-center gap-2 text-ink-900 dark:text-neutral-100">
                    <Search className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
                    检索参数
                  </span>
                </Divider>
                <Form.Item name="retrieve_top_n" label="检索 TopN">
                  <Input inputMode="numeric" autoComplete="off" />
                </Form.Item>
                <Form.Item name="rerank_top_n" label="重排 TopN">
                  <Input inputMode="numeric" autoComplete="off" />
                </Form.Item>
                <Form.Item name="similarity_threshold" label="相似度阈值">
                  <Input inputMode="decimal" autoComplete="off" />
                </Form.Item>
              </div>

              <Form.Item className="!mb-0 !mt-2">
                <Button type="primary" htmlType="submit" loading={saving} disabled={loading} size="large">
                  保存配置
                </Button>
              </Form.Item>
            </Form>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}
