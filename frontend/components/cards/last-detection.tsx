'use client'

import { Boxes, GlassWater, Newspaper, Package, ScanEye, Layers, Clock } from 'lucide-react'
import { Panel } from '@/components/panel'
import type { Telemetry, WasteCategory } from '@/lib/types'
import { CATEGORY_MAP } from '@/lib/types'

const ICONS: Record<WasteCategory, typeof Package> = {
  PLASTIC: Package,
  PAPER: Newspaper,
  METAL: Boxes,
  GLASS: GlassWater,
  CARDBOARD: Layers,
}

export function LastDetectionCard({ telemetry }: { telemetry: Telemetry }) {
  const det = telemetry.lastDetection
  const isSeed = det.id === 'seed'
  const meta = CATEGORY_MAP[det.category] ?? CATEGORY_MAP.PLASTIC
  const Icon = ICONS[det.category] ?? Package
  
  let formattedTime = 'Just now'
  try {
    if (det.timestamp && !isSeed) {
      formattedTime = new Date(det.timestamp).toLocaleTimeString('en-US', { hour12: true })
    }
  } catch {
    formattedTime = 'Just now'
  }

  return (
    <Panel title="Last Classified Item" icon={<ScanEye className="size-4 text-sky-600" />}>
      <div className="flex flex-col items-center gap-4 text-center">
        <ConfidenceRing value={isSeed ? 0 : det.confidence} color={meta.color}>
          <div
            className="grid size-16 place-items-center rounded-2xl transition-all duration-300 shadow-sm"
            style={{
              background: isSeed ? 'rgba(0,0,0,0.04)' : `${meta.color}15`,
              color: isSeed ? '#94a3b8' : meta.color,
            }}
          >
            <Icon className="size-8" />
          </div>
        </ConfidenceRing>

        <div>
          <p className="text-lg font-bold tracking-tight text-slate-900">
            {isSeed ? 'Waiting for First Detection' : meta.label}
          </p>
          <p className="font-mono text-xs text-muted-foreground mt-0.5">
            {isSeed ? 'Place trash item in target box' : `${det.confidence.toFixed(1)}% YOLO Confidence`}
          </p>
        </div>

        {!isSeed ? (
          <div className="flex items-center gap-3">
            <span
              className="rounded-lg px-2.5 py-1 font-mono text-xs font-bold ring-1 ring-inset"
              style={{ background: `${meta.color}12`, color: meta.color, borderColor: `${meta.color}40` }}
            >
              [{det.code}] ➔ {meta.bin}
            </span>
            <span suppressHydrationWarning className="font-mono text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="size-3 text-slate-400" />
              {formattedTime}
            </span>
          </div>
        ) : (
          <span className="rounded-md bg-slate-100 px-3 py-1 font-mono text-[11px] text-slate-500">
            Awaiting 5s YOLO Scan
          </span>
        )}
      </div>
    </Panel>
  )
}

function ConfidenceRing({
  value,
  color,
  children,
}: {
  value: number
  color: string
  children: React.ReactNode
}) {
  const r = 46
  const c = 2 * Math.PI * r
  const offset = c - (Math.max(0, Math.min(100, value)) / 100) * c
  return (
    <div className="relative grid size-28 place-items-center">
      <svg className="absolute inset-0 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="var(--secondary)" strokeWidth="6" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      {children}
    </div>
  )
}
