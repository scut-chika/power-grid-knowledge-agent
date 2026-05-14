import { Button, Form, Input, message } from 'antd'
import { motion } from 'framer-motion'
import { Lock, Sparkles, User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'
import { saveAuth } from '../store/auth'
import { cn } from '../lib/utils'

export default function LoginPage() {
  const nav = useNavigate()

  async function onFinish(values: any) {
    try {
      const data = await login(values.username, values.password)
      saveAuth(data.token, data.role)
      message.success('登录成功')
      nav('/')
    } catch {
      message.error('登录失败，请检查账号密码')
    }
  }

  return (
    <div className="relative h-full min-h-0 overflow-y-auto bg-[#0a0a0b] text-white">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.55]"
        style={{
          background:
            'radial-gradient(1200px 600px at 20% -10%, oklch(0.55 0.14 175 / 0.35), transparent 55%), radial-gradient(900px 500px at 100% 20%, oklch(0.45 0.12 250 / 0.25), transparent 50%), radial-gradient(800px 400px at 50% 100%, oklch(0.35 0.08 175 / 0.2), transparent 45%)',
        }}
      />
      <div className="app-grain absolute inset-0 opacity-[0.12]" />

      <div className="relative z-10 mx-auto flex min-h-full max-w-6xl flex-col lg:flex-row">
        <motion.section
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-1 flex-col justify-center px-8 py-14 lg:px-14"
        >
          <div className="mb-10 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-600 shadow-lg shadow-brand-600/30">
              <Sparkles className="h-5 w-5 text-white" strokeWidth={2.2} aria-hidden />
            </div>
            <div>
              <p className="font-display text-lg font-semibold tracking-tight">电网知识智能体</p>
              <p className="text-sm text-neutral-400">Enterprise Knowledge Graph</p>
            </div>
          </div>
          <h1 className="max-w-xl font-display text-4xl font-semibold leading-tight tracking-tight md:text-5xl">
            以对话驱动
            <span className="bg-gradient-to-r from-brand-400 to-teal-200 bg-clip-text text-transparent">
              {' '}
              运行知识
            </span>
          </h1>
          <p className="mt-5 max-w-md text-[16px] leading-relaxed text-neutral-400">
            统一检索规程、图纸与图谱关系，为调度与运维提供可引用、可追溯的智能答复。
          </p>
          <div className="mt-10 hidden gap-3 text-xs text-neutral-500 lg:flex">
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">RAG 检索</span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Neo4j 图谱</span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">流式输出</span>
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-1 items-center justify-center px-6 pb-16 pt-4 lg:px-12 lg:py-14"
        >
          <div
            className={cn(
              'w-full max-w-[400px] rounded-3xl border border-white/10 bg-white/[0.06] p-8 shadow-2xl backdrop-blur-2xl',
              'ring-1 ring-white/10'
            )}
          >
            <div className="mb-6">
              <p className="text-sm font-medium text-neutral-300">欢迎回来</p>
              <h2 className="mt-1 font-display text-2xl font-semibold tracking-tight">登录控制台</h2>
              <p className="mt-2 text-xs leading-relaxed text-neutral-500">
                对话与系统设置接口需要登录后的令牌。若曾修改 <code className="text-neutral-400">.env</code> 里的{' '}
                <code className="text-neutral-400">SECRET_KEY</code>，请重新登录。默认账号 admin / admin123。
              </p>
            </div>
            <Form layout="vertical" onFinish={onFinish} initialValues={{ username: 'admin', password: 'admin123' }}>
              <Form.Item
                name="username"
                label={<span className="text-neutral-300">用户名</span>}
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input
                  size="large"
                  prefix={<User className="h-4 w-4 text-neutral-400" aria-hidden />}
                  className="!rounded-xl !border-white/15 !bg-white/10 !text-white placeholder:!text-neutral-500"
                />
              </Form.Item>
              <Form.Item
                name="password"
                label={<span className="text-neutral-300">密码</span>}
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password
                  size="large"
                  prefix={<Lock className="h-4 w-4 text-neutral-400" aria-hidden />}
                  className="!rounded-xl !border-white/15 !bg-white/10 !text-white placeholder:!text-neutral-500"
                />
              </Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                className="!mt-2 !h-11 !rounded-xl !font-semibold !shadow-lg !shadow-brand-600/25"
              >
                进入系统
              </Button>
            </Form>
          </div>
        </motion.section>
      </div>
    </div>
  )
}
