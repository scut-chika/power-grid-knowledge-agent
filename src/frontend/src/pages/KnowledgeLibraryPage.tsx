import { Button, Card, Select, Space, Table, Tag, Upload, message } from 'antd'
import type { UploadFile } from 'antd/es/upload/interface'
import { motion } from 'framer-motion'
import { BookMarked, RefreshCw, UploadCloud } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { buildKnowledge, getBuildStatus, getFiles, uploadFiles } from '../services/api'
import { getRole } from '../store/auth'

const FILE_TYPES = [
  { label: '规程 / 文档 (documents)', value: 'documents' },
  { label: '表格 (tables)', value: 'tables' },
  { label: '图纸 (drawings)', value: 'drawings' },
  { label: '扫描件 (scans)', value: 'scans' },
] as const

function parseMeta(row: any) {
  try {
    if (row.metadata_json && typeof row.metadata_json === 'string') {
      return JSON.parse(row.metadata_json) as Record<string, unknown>
    }
  } catch {
    /* ignore */
  }
  return {}
}

export default function KnowledgeLibraryPage() {
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [fileType, setFileType] = useState<string>('documents')
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [task, setTask] = useState<any>(null)
  const [indexing, setIndexing] = useState(false)
  const isAdmin = getRole() === 'admin'

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getFiles({ page: 1, page_size: 100 })
      setRows(data.items || [])
    } catch {
      message.error('加载文档列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function onUpload() {
    const raw = fileList.map((f) => f.originFileObj).filter(Boolean) as File[]
    if (!raw.length) {
      message.warning('请先选择文件')
      return
    }
    setUploading(true)
    try {
      await uploadFiles(raw, fileType)
      message.success('已上传并写入登记库，可进行「增量编入」以向量化并更新图谱')
      setFileList([])
      await load()
    } catch {
      message.error('上传失败，请检查网络或登录状态')
    } finally {
      setUploading(false)
    }
  }

  async function runIncremental() {
    setIndexing(true)
    try {
      const data = await buildKnowledge('incremental')
      setTask(data)
      message.success('已提交增量构建任务，向量化与图谱由后台流水线处理')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '提交失败')
    } finally {
      setIndexing(false)
    }
  }

  async function refreshTask() {
    if (!task?.task_id) return
    try {
      const data = await getBuildStatus(task.task_id)
      setTask(data)
    } catch {
      message.error('无法获取任务状态')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex h-full min-h-0 flex-col gap-4 overflow-hidden"
    >
      <div className="rounded-2xl border border-neutral-200/80 bg-white/70 px-5 py-4 shadow-[var(--shadow-soft)] backdrop-blur-md dark:border-white/10 dark:bg-zinc-900/40 md:px-6">
        <h2 className="font-display text-xl font-semibold tracking-tight text-ink-900 dark:text-neutral-100 md:text-2xl">
          知识文库
        </h2>
        <p className="mt-1.5 max-w-3xl text-[15px] leading-relaxed text-ink-700 dark:text-neutral-400">
          上传原始知识文档后，数据会写入登记库与 <code className="rounded bg-black/[0.06] px-1 dark:bg-white/10">data/raw</code>。
          点击「增量编入知识库」将触发后台流水线：解析、向量化并同步知识图谱（与「构建调度」中的增量任务相同）。
        </p>
      </div>

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(0,380px)_1fr] lg:gap-5">
        <Card
          className="!flex !min-h-0 !flex-col !border-neutral-200/80 dark:!border-white/10 dark:!bg-zinc-900/35"
          title={
            <span className="inline-flex items-center gap-2 font-display text-[15px] font-semibold">
              <UploadCloud className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
              上传文档
            </span>
          }
        >
          <Space direction="vertical" className="w-full" size="middle">
            <div>
              <div className="mb-1.5 text-sm font-medium text-ink-700 dark:text-neutral-300">归档类型</div>
              <Select
                className="w-full"
                value={fileType}
                onChange={setFileType}
                options={FILE_TYPES.map((x) => ({ label: x.label, value: x.value }))}
              />
            </div>
            <Upload.Dragger
              multiple
              fileList={fileList}
              beforeUpload={() => false}
              onChange={({ fileList: fl }) => setFileList(fl)}
              className="[&_.ant-upload-drag]:!rounded-xl"
            >
              <p className="text-sm text-ink-700 dark:text-neutral-300">拖拽文件到此处，或点击选择</p>
              <p className="mt-1 text-xs text-ink-700/70 dark:text-neutral-500">支持多文件；将保存至对应 raw 子目录并登记元数据</p>
            </Upload.Dragger>
            <Button type="primary" block size="large" loading={uploading} onClick={() => void onUpload()}>
              上传到文库
            </Button>
            <Button
              type="default"
              block
              size="large"
              loading={indexing}
              className="!border-brand-600/40 !text-brand-800 dark:!text-brand-300"
              onClick={() => void runIncremental()}
            >
              增量编入知识库（向量化 + 图谱）
            </Button>
            <div className="flex flex-wrap items-center gap-2 rounded-xl bg-neutral-100/80 px-3 py-2 text-xs dark:bg-white/[0.06]">
              <span className="text-ink-700 dark:text-neutral-400">最近任务：</span>
              {task?.status ? (
                <Tag className="!m-0">{task.status}</Tag>
              ) : (
                <span className="text-neutral-500">暂无</span>
              )}
              <Button type="link" size="small" className="!p-0" onClick={() => void refreshTask()}>
                刷新状态
              </Button>
            </div>
            {isAdmin ? (
              <p className="text-xs text-neutral-500 dark:text-neutral-500">
                全量重建请前往「构建调度」；普通用户仅可执行增量编入。
              </p>
            ) : null}
          </Space>
        </Card>

        <Card
          className="!flex !min-h-0 !flex-1 !flex-col !overflow-hidden !border-neutral-200/80 dark:!border-white/10 dark:!bg-zinc-900/35"
          classNames={{ body: '!flex !min-h-0 !flex-1 !flex-col !overflow-hidden !p-4 md:!p-5' }}
          title={
            <span className="inline-flex items-center gap-2 font-display text-[15px] font-semibold">
              <BookMarked className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden />
              文库索引
            </span>
          }
          extra={
            <Button type="text" size="small" icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={() => void load()}>
              刷新列表
            </Button>
          }
        >
          <div className="min-h-0 flex-1 overflow-auto">
            <Table
              rowKey="id"
              size="small"
              loading={loading}
              dataSource={rows}
              pagination={{ pageSize: 15, showSizeChanger: true }}
              columns={[
                { title: '文件名', dataIndex: 'file_name', ellipsis: true },
                { title: '类型', dataIndex: 'file_type', width: 110 },
                { title: '厂站', dataIndex: 'station_name', width: 100, render: (v) => v || '—' },
                {
                  title: '上传者',
                  key: 'uploader',
                  width: 100,
                  render: (_, row) => {
                    const m = parseMeta(row)
                    return (m.uploader as string) || '—'
                  },
                },
                {
                  title: '入库时间',
                  dataIndex: 'created_at',
                  width: 180,
                  render: (v: string) => (v ? new Date(v).toLocaleString() : '—'),
                },
              ]}
            />
          </div>
        </Card>
      </div>
    </motion.div>
  )
}
