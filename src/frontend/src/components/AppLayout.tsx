import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { useState } from 'react'
import {
  Factory,
  LayoutDashboard,
  LibraryBig,
  MessageSquare,
  Monitor,
  Moon,
  Network,
  PanelLeftClose,
  PanelLeft,
  Settings2,
  Sparkles,
  Sun,
} from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { useThemeMode, type ThemeMode } from '../context/ThemeContext'
import { cn } from '../lib/utils'

const nav = [
  { to: '/', key: '/', label: '工作台', icon: LayoutDashboard },
  { to: '/library', key: '/library', label: '知识文库', icon: LibraryBig },
  { to: '/data', key: '/data', label: '构建调度', icon: Factory },
  { to: '/graph', key: '/graph', label: '图谱浏览', icon: Network },
  { to: '/chat', key: '/chat', label: '智能对话', icon: MessageSquare },
  { to: '/settings', key: '/settings', label: '系统设置', icon: Settings2 },
] as const

const titles: Record<string, string> = {
  '/': '运行概览',
  '/library': '知识文库',
  '/data': '构建调度',
  '/graph': '图谱浏览',
  '/chat': '智能对话',
  '/settings': '系统设置',
}

const themeButtons: { mode: ThemeMode; icon: typeof Sun; label: string }[] = [
  { mode: 'light', icon: Sun, label: '浅色' },
  { mode: 'dark', icon: Moon, label: '暗色' },
  { mode: 'system', icon: Monitor, label: '跟随系统' },
]

export default function AppLayout({ children }: { children: ReactNode }) {
  const loc = useLocation()
  const { mode: themeMode, resolved, setMode } = useThemeMode()
  const [collapsed, setCollapsed] = useState(false)
  const title = titles[loc.pathname] ?? '电网知识智能体'
  const isChat = loc.pathname === '/chat'
  const isSettings = loc.pathname === '/settings'
  const isLibrary = loc.pathname === '/library'
  const isLightChrome = resolved === 'light'

  return (
    <div
      className={cn(
        'app-grain relative flex h-[100dvh] max-h-[100dvh] min-h-0 w-full overflow-hidden bg-gradient-to-br from-surface-50 via-surface-100 to-surface-200',
        'dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950'
      )}
    >
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 76 : 268 }}
        transition={{ type: 'spring', stiffness: 420, damping: 38 }}
        className={cn(
          'relative z-20 flex h-full max-h-[100dvh] shrink-0 flex-col shadow-[4px_0_48px_rgba(0,0,0,0.35)]',
          isLightChrome
            ? 'border-r border-neutral-200/90 bg-neutral-100 text-neutral-800'
            : 'border-r border-white/10 bg-[#171717] text-neutral-200'
        )}
      >
        <div
          className={cn(
            'flex shrink-0 items-center gap-3 px-3 pb-3 pt-4',
            isLightChrome ? 'border-b border-neutral-200/90' : 'border-b border-white/[0.08]',
            collapsed && 'flex-col justify-center px-2 pb-3 pt-4'
          )}
        >
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-600 text-white shadow-lg shadow-brand-600/25">
            <Sparkles className="h-[22px] w-[22px]" strokeWidth={2.2} aria-hidden />
          </div>
          {!collapsed && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-w-0 flex-1">
              <div
                className={cn(
                  'truncate font-display text-[14px] font-semibold leading-snug tracking-tight',
                  isLightChrome ? 'text-neutral-900' : 'text-white'
                )}
              >
                电网知识智能体
              </div>
              <div
                className={cn(
                  'mt-0.5 truncate text-[11px] leading-relaxed',
                  isLightChrome ? 'text-neutral-500' : 'text-neutral-500'
                )}
              >
                Enterprise Knowledge
              </div>
            </motion.div>
          )}
        </div>

        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-2 pt-3" aria-label="主导航">
          {nav.map((item) => {
            const active = loc.pathname === item.key
            const Icon = item.icon
            return (
              <Link
                key={item.key}
                to={item.to}
                className={cn(
                  'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] font-medium outline-none transition-colors duration-150',
                  isLightChrome
                    ? 'text-neutral-600 hover:bg-black/[0.05] hover:text-neutral-900 focus-visible:ring-2 focus-visible:ring-brand-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-100'
                    : 'text-neutral-400 hover:bg-white/[0.06] hover:text-neutral-100 focus-visible:ring-2 focus-visible:ring-brand-400/80 focus-visible:ring-offset-2 focus-visible:ring-offset-[#171717]',
                  active &&
                    (isLightChrome
                      ? 'bg-white text-neutral-900 shadow-sm ring-1 ring-neutral-200/80'
                      : 'bg-white/[0.12] text-white')
                )}
              >
                <Icon
                  className={cn(
                    'h-[18px] w-[18px] shrink-0 transition-transform duration-150 group-hover:scale-105',
                    active && 'text-brand-600 dark:text-brand-400'
                  )}
                  strokeWidth={2}
                  aria-hidden
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        <div
          className={cn(
            'space-y-2 border-t p-2',
            isLightChrome ? 'border-neutral-200/90' : 'border-white/[0.08]'
          )}
          role="group"
          aria-label="外观"
        >
          <div
            className={cn(
              'flex justify-center gap-0.5 rounded-xl p-1',
              isLightChrome ? 'bg-white/80 ring-1 ring-neutral-200/80' : 'bg-white/[0.06]'
            )}
          >
            {themeButtons.map(({ mode, icon: Icon, label }) => {
              const on = themeMode === mode
              return (
                <button
                  key={mode}
                  type="button"
                  title={label}
                  aria-label={label}
                  aria-pressed={on}
                  onClick={() => setMode(mode)}
                  className={cn(
                    'flex h-9 min-w-9 flex-1 items-center justify-center rounded-lg transition-colors',
                    on
                      ? isLightChrome
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'bg-white/[0.14] text-white'
                      : isLightChrome
                        ? 'text-neutral-500 hover:bg-neutral-100 hover:text-neutral-800'
                        : 'text-neutral-500 hover:bg-white/[0.08] hover:text-neutral-200'
                  )}
                >
                  <Icon className="h-[17px] w-[17px]" strokeWidth={2.2} aria-hidden />
                </button>
              )
            })}
          </div>

          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className={cn(
              'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[13px] font-medium transition-colors focus-visible:outline-none',
              isLightChrome
                ? 'text-neutral-600 hover:bg-black/[0.05] hover:text-neutral-900 focus-visible:ring-2 focus-visible:ring-brand-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-100'
                : 'text-neutral-400 hover:bg-white/[0.06] hover:text-neutral-100 focus-visible:ring-2 focus-visible:ring-brand-400/80 focus-visible:ring-offset-2 focus-visible:ring-offset-[#171717]',
              collapsed && 'justify-center px-0'
            )}
            aria-expanded={!collapsed}
            aria-label={collapsed ? '展开侧栏' : '收起侧栏'}
          >
            {collapsed ? (
              <PanelLeft className="h-[18px] w-[18px] shrink-0" strokeWidth={2} aria-hidden />
            ) : (
              <>
                <PanelLeftClose className="h-[18px] w-[18px] shrink-0" strokeWidth={2} aria-hidden />
                <span>收起侧栏</span>
              </>
            )}
          </button>
        </div>
      </motion.aside>

      <div className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <header
          className={cn(
            'relative z-10 flex min-h-[60px] shrink-0 items-center justify-between gap-4 border-b px-5 py-3.5',
            'backdrop-blur-xl supports-[backdrop-filter]:bg-white/40',
            isLightChrome
              ? 'border-neutral-200/70 bg-white/55'
              : 'border-white/10 bg-zinc-900/50 text-white supports-[backdrop-filter]:bg-zinc-900/40'
          )}
        >
          <div className="min-w-0 space-y-1 pt-0.5">
            <h1
              className={cn(
                'truncate font-display text-[15px] font-semibold leading-snug tracking-tight',
                isLightChrome ? 'text-ink-900' : 'text-white'
              )}
            >
              {title}
            </h1>
            <p
              className={cn(
                'truncate text-xs leading-relaxed',
                isLightChrome ? 'text-ink-700/80' : 'text-neutral-400'
              )}
            >
              基于 AI 的电网运行知识图谱与检索中枢
            </p>
          </div>
          <motion.div
            className={cn(
              'hidden items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium shadow-sm sm:flex',
              isLightChrome
                ? 'border-neutral-200/80 bg-white/70 text-ink-700'
                : 'border-white/10 bg-white/10 text-neutral-200'
            )}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-500/50 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-500" />
            </span>
            服务就绪
          </motion.div>
        </header>

        <main
          className={cn(
            'relative min-h-0 flex-1',
            isChat
              ? 'overflow-hidden p-0'
              : isSettings || isLibrary
                ? 'flex flex-col overflow-hidden px-5 pb-5 pt-6 md:px-6 md:pb-6 md:pt-7'
                : 'overflow-auto px-5 pb-5 pt-6 md:px-6 md:pb-6 md:pt-7'
          )}
        >
          {children}
        </main>
      </div>
    </div>
  )
}
