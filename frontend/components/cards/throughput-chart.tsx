'use client'

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { TrendingUp } from 'lucide-react'
import { Panel } from '@/components/panel'
import type { Telemetry } from '@/lib/types'

const DEFAULT_HOURLY = [
  { hour: '08:00', items: 0 },
  { hour: '09:00', items: 0 },
  { hour: '10:00', items: 0 },
  { hour: '11:00', items: 0 },
  { hour: '12:00', items: 0 },
  { hour: '13:00', items: 0 },
  { hour: '14:00', items: 0 },
  { hour: '15:00', items: 0 },
  { hour: '16:00', items: 0 },
  { hour: '17:00', items: 0 },
]

export function ThroughputChart({ telemetry }: { telemetry?: Telemetry }) {
  const chartData = telemetry?.hourlyThroughput && telemetry.hourlyThroughput.length > 0
    ? telemetry.hourlyThroughput
    : DEFAULT_HOURLY

  const totalSortedToday = chartData.reduce((acc, curr) => acc + curr.items, 0)
  const peakHourly = Math.max(...chartData.map((d) => d.items), 0)

  return (
    <Panel
      title="Hourly Waste Throughput"
      icon={<TrendingUp className="size-4 text-sky-600" />}
      action={
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-bold text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md border border-sky-200">
            PEAK: {peakHourly} ITEMS/HR
          </span>
          <span className="font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
            TOTAL: {totalSortedToday}
          </span>
        </div>
      }
    >
      <div className="h-60 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#e2e8f0" strokeDasharray="3 3" />
            <XAxis
              dataKey="hour"
              tickLine={false}
              axisLine={{ stroke: '#cbd5e1' }}
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace', fontWeight: 600 }}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={{ stroke: '#cbd5e1' }}
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace', fontWeight: 600 }}
            />
            <Tooltip
              cursor={{ fill: 'rgba(2,132,199,0.06)' }}
              contentStyle={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: 12,
                fontSize: 12,
                boxShadow: '0 4px 20px -2px rgba(0,0,0,0.08)',
              }}
              labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
              itemStyle={{ color: '#0284c7', fontWeight: 'bold' }}
              formatter={(val: any) => [`${val} items sorted`, 'Throughput']}
            />
            <Bar
              dataKey="items"
              fill="#0284c7"
              radius={[6, 6, 0, 0]}
              maxBarSize={32}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2.5 flex items-center justify-between border-t border-slate-100 pt-2 text-[11px] font-mono text-slate-500">
        <span>Dynamic SQLite Aggregation by Hour</span>
        <span>Live Telemetry WebSocket Synced</span>
      </div>
    </Panel>
  )
}
