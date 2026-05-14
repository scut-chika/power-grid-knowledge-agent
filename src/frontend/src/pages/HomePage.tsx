import { Card, Col, Row, Statistic } from 'antd'
import { motion } from 'framer-motion'
import { Activity, Cpu, Database, Layers } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getSystemStatus } from '../services/api'
import { cn } from '../lib/utils'

const tiles = [
  { key: 'sqlite', title: 'SQLite', icon: Database, accent: 'from-sky-500/15 to-sky-600/5 ring-sky-500/20' },
  { key: 'neo4j', title: 'Neo4j', icon: Layers, accent: 'from-violet-500/15 to-violet-600/5 ring-violet-500/20' },
  { key: 'milvus', title: 'Milvus', icon: Cpu, accent: 'from-amber-500/15 to-amber-600/5 ring-amber-500/20' },
  { key: 'llm', title: 'LLM 配置', icon: Activity, accent: 'from-brand-500/20 to-brand-600/5 ring-brand-500/25' },
] as const

const ease = [0.22, 1, 0.36, 1] as const

export default function HomePage() {
  const [status, setStatus] = useState<any>({})

  useEffect(() => {
    getSystemStatus().then(setStatus).catch(() => setStatus({}))
  }, [])

  const valueMap: Record<string, string> = {
    sqlite: status.sqlite || 'unknown',
    neo4j: status.neo4j || 'unknown',
    milvus: status.milvus || 'unknown',
    llm: status.llm || 'pending',
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease }}
      >
        <div className="rounded-2xl border border-neutral-200/80 bg-white/70 p-6 shadow-[var(--shadow-soft)] backdrop-blur-md md:p-8">
          <h2 className="font-display text-2xl font-semibold tracking-tight text-ink-900 md:text-3xl">
            运行概览
          </h2>
          <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-ink-700">
            快速确认核心数据与模型依赖是否就绪，保障检索、图谱与对话链路稳定。
          </p>
        </div>
      </motion.div>

      <Row gutter={[16, 16]}>
        {tiles.map((t, i) => {
          const Icon = t.icon
          return (
            <Col xs={24} sm={12} lg={6} key={t.key}>
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.38, delay: 0.06 + i * 0.07, ease }}
              >
                <Card
                  bordered={false}
                  className="!overflow-hidden !border !border-neutral-200/70 !bg-white/75 !shadow-[var(--shadow-glass)]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-ink-700/70">
                        {t.title}
                      </p>
                      <Statistic
                        value={valueMap[t.key]}
                        valueStyle={{
                          fontSize: 22,
                          fontWeight: 600,
                          color: '#14181f',
                          fontFamily: '"Sora", "Plus Jakarta Sans", sans-serif',
                        }}
                      />
                    </div>
                    <div
                      className={cn(
                        'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ring-1',
                        t.accent
                      )}
                    >
                      <Icon className="h-5 w-5 text-ink-900/85" strokeWidth={2} aria-hidden />
                    </div>
                  </div>
                </Card>
              </motion.div>
            </Col>
          )
        })}
      </Row>
    </div>
  )
}
