'use client'

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { PieChart as PieIcon } from 'lucide-react'
import { Panel } from '@/components/panel'
import { CATEGORIES } from '@/lib/types'
import type { Telemetry } from '@/lib/types'

const COLOR_HEX: Record<string, string> = {
  PLASTIC: '#0284c7',
  PAPER: '#059669',
  METAL: '#d97706',
  GLASS: '#7c3aed',
  CARDBOARD: '#ea580c',
}

export function StatisticsCard({ telemetry }: { telemetry: Telemetry }) {
  const data = CATEGORIES.map((c) => ({
    name: c.label,
    key: c.key,
    value: telemetry.counts[c.key] ?? 0,
    color: COLOR_HEX[c.key],
    bin: c.bin,
  }))
  const total = data.reduce((sum, d) => sum + d.value, 0)

  return (
    <Panel title="Today's Segregation Analytics" icon={<PieIcon className="size-4 text-sky-600" />}>
      {/* 2D Category Progress Meters */}
      <div className="flex flex-col gap-2 mb-3">
        {data.map((d) => {
          const pct = total > 0 ? Math.round((d.value / total) * 100) : 0
          return (
            <div key={d.key} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 font-medium text-slate-800">
                  <span className="size-2 rounded-sm" style={{ background: d.color }} />
                  <span>{d.name}</span>
                </span>
                <span className="font-mono text-xs tabular-nums text-slate-500">
                  {d.value} items ({pct}%)
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${pct}%`, background: d.color }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="relative mx-auto h-40 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={50}
              outerRadius={72}
              paddingAngle={3}
              stroke="none"
              isAnimationActive={false}
            >
              {data.map((d) => (
                <Cell key={d.key} fill={COLOR_HEX[d.key]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: 12,
                fontSize: 12,
                boxShadow: '0 4px 20px -2px rgba(0,0,0,0.08)',
              }}
              labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
              itemStyle={{ color: '#0f172a' }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center">
          <div className="text-center">
            <p className="font-mono text-2xl font-bold tabular-nums text-slate-900">{total}</p>
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Total Today</p>
          </div>
        </div>
      </div>
    </Panel>
  )
}
