import { Card } from 'antd'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { motion } from 'framer-motion'
import { Share2 } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { getGraph } from '../services/api'

echarts.use([GraphChart, TooltipComponent, CanvasRenderer])

export default function GraphPage() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const chart = echarts.init(ref.current)
    getGraph().then((data) => {
      chart.setOption({
        tooltip: {},
        series: [
          {
            type: 'graph',
            layout: 'force',
            roam: true,
            data: (data.nodes || []).map((n: any) => ({ id: n.id, name: n.name, value: n.type })),
            links: (data.links || []).map((l: any) => ({
              source: l.source,
              target: l.target,
              label: { show: true, formatter: l.relation },
            })),
            label: { show: true },
            force: { repulsion: 120 },
          },
        ],
      })
    })
    return () => chart.dispose()
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      <Card
        title={
          <span className="inline-flex items-center gap-2 font-display text-[15px] font-semibold">
            <Share2 className="h-4 w-4 text-brand-600" aria-hidden />
            知识图谱可视化
          </span>
        }
        className="!overflow-hidden"
      >
        <div ref={ref} className="h-[min(60vh,560px)] min-h-[420px] w-full rounded-xl bg-surface-50/50" />
      </Card>
    </motion.div>
  )
}
