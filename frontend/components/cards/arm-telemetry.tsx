'use client'

import { Bot, Compass, CheckCircle2 } from 'lucide-react'
import { Panel } from '@/components/panel'
import type { ArmAngles, Telemetry } from '@/lib/types'
import { CATEGORIES } from '@/lib/types'

const JOINTS: { key: keyof ArmAngles; label: string; max: number; note?: (v: number) => string }[] = [
  { key: 'base', label: 'Base (Horizontal Pan)', max: 180 },
  { key: 'shoulder', label: 'Shoulder (Vertical Lift)', max: 180 },
  { key: 'elbow', label: 'Elbow (Reach Extension)', max: 180 },
  { key: 'wrist', label: 'Wrist (Elevation Pitch)', max: 180 },
  {
    key: 'gripper',
    label: 'Claw / Hand (Gripper)',
    max: 180,
    note: (v) => (v <= 25 ? 'Closed (Holding)' : v > 100 ? 'Open (Released)' : 'Positioning'),
  },
]

export function ArmTelemetryCard({ telemetry }: { telemetry: Telemetry }) {
  const isOperating = telemetry.state === 'OPERATING'
  const activeCategory = telemetry.lastDetection.category

  return (
    <Panel
      title="Robotic Arm 6-DOF Telemetry & Servo Angles"
      icon={<Bot className="size-4 text-sky-600" />}
      action={
        <span className="font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
          PCA9685 · 19200 BAUD
        </span>
      }
    >
      {/* Bin Destination Layout Visualizer */}
      <div className="mb-4 rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 shadow-xs">
        <div className="mb-2.5 flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-2">
            <Compass className="size-4 text-sky-600" />
            <span>Predefined Bin Destination Layout:</span>
          </span>
          <span className="font-mono text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
            {isOperating ? 'Arm Throwing...' : 'Arm at Home (90°)'}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {CATEGORIES.map((c) => {
            const isActive = isOperating && activeCategory === c.key

            return (
              <div
                key={c.key}
                className="flex flex-col items-center justify-center rounded-lg border p-2.5 text-center transition-all duration-300 shadow-xs"
                style={{
                  borderColor: isActive ? c.color : '#e2e8f0',
                  background: isActive ? `${c.color}15` : '#ffffff',
                  boxShadow: isActive ? `0 0 12px -2px ${c.color}` : 'none',
                }}
              >
                <span className="font-mono text-xs font-extrabold block" style={{ color: c.color }}>
                  [{c.code}] {c.label}
                </span>
                <span className="text-[11px] font-mono font-bold text-slate-700 mt-1 block">
                  {c.bin}
                </span>
                {isActive && (
                  <span className="mt-1 flex items-center gap-1 font-mono text-[10px] font-extrabold text-sky-700 uppercase tracking-wider animate-pulse">
                    <CheckCircle2 className="size-3 text-sky-600" /> Target
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Joint Angle Telemetry Bars */}
      <div className="flex flex-col gap-2.5">
        {JOINTS.map((j) => {
          const value = telemetry.arm[j.key] ?? 90
          const pct = Math.min(100, Math.max(0, (value / j.max) * 100))

          return (
            <div
              key={j.key}
              className="rounded-xl bg-white p-3 border border-slate-200 shadow-xs"
            >
              <div className="mb-2 flex items-baseline justify-between">
                <span className="text-xs font-bold text-slate-800">{j.label}</span>
                <div className="flex items-center gap-2">
                  {j.note && (
                    <span className="text-xs font-semibold text-slate-500">{j.note(value)}</span>
                  )}
                  <span className="font-mono text-sm font-extrabold tabular-nums text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                    {Math.round(value)}°
                  </span>
                </div>
              </div>

              <div className="h-2.5 overflow-hidden rounded-full bg-slate-100 border border-slate-200">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-sky-500 to-blue-600 transition-[width] duration-300 ease-out"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </Panel>
  )
}
