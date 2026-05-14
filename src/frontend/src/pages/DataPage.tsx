import { Button, Card, Space, Tag, Typography, message } from 'antd'
import { motion } from 'framer-motion'
import { Factory, FileStack } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { buildKnowledge, getBuildStatus } from '../services/api'
import { getRole } from '../store/auth'

export default function DataPage() {
  const [task, setTask] = useState<any>(null)
  const isAdmin = getRole() === 'admin'

  async function triggerBuild(mode: 'incremental' | 'full') {
    try {
      const data = await buildKnowledge(mode)
      setTask(data)
      message.success(`已触发构建任务：${data.task_id}`)
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '触发失败')
    }
  }

  async function refreshTask() {
    if (!task?.task_id) return
    const data = await getBuildStatus(task.task_id)
    setTask(data)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      <Space direction="vertical" size="middle" className="w-full">
        <div className="rounded-2xl border border-neutral-200/80 bg-white/70 px-5 py-4 shadow-[var(--shadow-soft)] backdrop-blur-md dark:border-white/10 dark:bg-zinc-900/40 md:px-6">
          <h2 className="font-display text-xl font-semibold tracking-tight text-ink-900 dark:text-neutral-100 md:text-2xl">
            构建调度
          </h2>
          <p className="mt-1.5 text-[15px] leading-relaxed text-ink-700 dark:text-neutral-400">
            集中触发向量库与图谱流水线任务。日常新增文档请先在{' '}
            <Link to="/library" className="font-medium text-brand-600 underline-offset-2 hover:underline dark:text-brand-400">
              知识文库
            </Link>{' '}
            上传，再使用增量构建纳入索引。
          </p>
        </div>

        <Card
          title={
            <span className="inline-flex items-center gap-2 font-display text-[15px] font-semibold">
              <Factory className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
              构建任务
            </span>
          }
        >
          <Space wrap>
            <Button type="primary" onClick={() => triggerBuild('incremental')}>
              增量构建
            </Button>
            {isAdmin ? (
              <Button danger onClick={() => triggerBuild('full')}>
                全量构建（管理员）
              </Button>
            ) : (
              <Typography.Text type="secondary" className="text-sm">
                全量构建仅管理员可用
              </Typography.Text>
            )}
            <Button onClick={refreshTask}>刷新任务状态</Button>
            {task && <Tag color="blue">{task.status || 'queued'}</Tag>}
          </Space>
          {task?.logs ? (
            <Typography.Paragraph className="!mb-0 !mt-3 text-xs text-neutral-500" copyable>
              {task.logs}
            </Typography.Paragraph>
          ) : null}
        </Card>

        <Card
          title={
            <span className="inline-flex items-center gap-2 font-display text-[15px] font-semibold">
              <FileStack className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
              说明
            </span>
          }
        >
          <Typography.Paragraph className="!mb-0 text-[15px] leading-relaxed text-ink-700 dark:text-neutral-300">
            增量 / 全量构建由后台线程执行，完成后向量库与图谱会更新。上传文件与文档列表已迁移至「知识文库」。
          </Typography.Paragraph>
        </Card>
      </Space>
    </motion.div>
  )
}
