'use client'

import { Activity, CircleCheck, TriangleAlert } from 'lucide-react'
import { Panel } from '@/components/panel'
import { cn } from '@/lib/utils'
import type { Telemetry } from '@/lib/types'

export function SystemHealthCard({ telemetry }: { telemetry: Telemetry }) {
  const okCount = telemetry.health.filter((h) => h.ok).length
  return (
    <Panel
      title="System Health & Diagnostics"
      icon={<Activity className="size-4 text-sky-600" />}
      action={
        <span className="font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
          {okCount}/{telemetry.health.length} SUBSYSTEMS OK
        </span>
      }
    >
      <ul className="flex flex-col gap-2.5">
        {telemetry.health.map((h) => (
          <li
            key={h.key}
            className="flex items-center gap-3.5 rounded-xl bg-white px-3.5 py-2.5 border border-slate-200 shadow-xs transition-all duration-150 hover:border-slate-300"
          >
            <span
              className={cn(
                'grid size-8 shrink-0 place-items-center rounded-lg border',
                h.ok
                  ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                  : 'bg-rose-50 text-rose-600 border-rose-200'
              )}
            >
              {h.ok ? <CircleCheck className="size-4" /> : <TriangleAlert className="size-4" />}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold text-slate-900">{h.label}</p>
              <p className="truncate font-mono text-xs text-slate-500 mt-0.5">{h.detail}</p>
            </div>
            <span
              className={cn(
                'size-2.5 rounded-full shrink-0',
                h.ok
                  ? 'bg-emerald-500 animate-status-blink'
                  : 'bg-rose-500'
              )}
            />
          </li>
        ))}
      </ul>
    </Panel>
  )
}
