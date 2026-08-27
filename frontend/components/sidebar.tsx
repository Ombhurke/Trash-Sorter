'use client'

import {
  Activity,
  BarChart3,
  Camera,
  Gamepad2,
  LayoutDashboard,
  Recycle,
  ScrollText,
  Settings,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Telemetry } from '@/lib/types'

export type TabKey =
  | 'dashboard'
  | 'camera'
  | 'manual'
  | 'stats'
  | 'history'
  | 'system'
  | 'settings'

const NAV: { key: TabKey; label: string; icon: typeof LayoutDashboard }[] = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'camera', label: 'Live Camera', icon: Camera },
  { key: 'manual', label: 'Manual Control', icon: Gamepad2 },
  { key: 'stats', label: 'Statistics', icon: BarChart3 },
  { key: 'history', label: 'History & Logs', icon: ScrollText },
  { key: 'system', label: 'System Status', icon: Activity },
  { key: 'settings', label: 'Settings', icon: Settings },
]

export function Sidebar({
  active,
  onChange,
  telemetry,
}: {
  active: TabKey
  onChange: (tab: TabKey) => void
  telemetry: Telemetry
}) {
  return (
    <aside className="glass sticky top-0 hidden h-dvh w-64 shrink-0 flex-col p-4 lg:flex border-r border-border bg-card/95">
      <div className="flex items-center gap-3 px-2 py-3">
        <div className="grid size-11 place-items-center rounded-xl bg-sky-50 text-sky-600 ring-1 ring-sky-200 shadow-sm">
          <Recycle className="size-6" />
        </div>
        <div className="leading-tight">
          <p className="text-lg font-black tracking-wider text-slate-900">SORT-X</p>
          <p className="text-[11px] leading-4 font-mono text-slate-500">Autonomous AI Waste<br />Segregation Platform</p>
        </div>
      </div>

      <nav className="mt-5 flex flex-1 flex-col gap-1.5">
        {NAV.map(({ key, label, icon: Icon }) => {
          const isActive = active === key
          return (
            <button
              key={key}
              type="button"
              onClick={() => onChange(key)}
              aria-current={isActive ? 'page' : undefined}
              className={cn(
                'group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition-all duration-150',
                isActive
                  ? 'bg-sky-50 text-sky-700 ring-1 ring-sky-200 shadow-xs font-bold'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 -translate-y-1/2 rounded-full bg-sky-600 w-1 shadow-xs" />
              )}
              <Icon className={cn('size-4.5', isActive ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-600')} />
              <span>{label}</span>
            </button>
          )
        })}
      </nav>

      <div className="glass mt-4 space-y-2.5 rounded-xl p-3.5 border border-border bg-slate-50/80">
        <ConnRow label="Backend API" active={telemetry.connected} text="Online" />
        <ConnRow label="WebSocket Feed" active={telemetry.wsActive} text="Live (19200)" />
      </div>
    </aside>
  )
}

function ConnRow({
  label,
  active,
  text,
}: {
  label: string
  active: boolean
  text: string
}) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-slate-500 font-medium">{label}</span>
      <span className="flex items-center gap-1.5 font-mono font-bold">
        <span
          className={cn(
            'size-2 rounded-full',
            active
              ? 'bg-emerald-500 shadow-xs animate-status-blink'
              : 'bg-rose-500 shadow-xs',
          )}
        />
        <span className={active ? 'text-emerald-600' : 'text-rose-600'}>
          {active ? text : 'Offline'}
        </span>
      </span>
    </div>
  )
}
