'use client'

import { useEffect, useState } from 'react'
import { ScrollText, RefreshCw } from 'lucide-react'
import { Panel } from '@/components/panel'
import { CATEGORY_MAP, type WasteCategory } from '@/lib/types'
import { api, type DetectionItem } from '@/services/api'

const COLOR_HEX: Record<string, string> = {
  PLASTIC: '#00f2fe',
  PAPER: '#10b981',
  METAL: '#f59e0b',
  GLASS: '#8b5cf6',
  CARDBOARD: '#f97316',
}

export function HistoryLog() {
  const [items, setItems] = useState<DetectionItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  async function loadDetections() {
    setLoading(true)
    try {
      const res = await api.getDetections(50)
      setItems(res.items)
    } catch (err) {
      console.error('Failed to load detections from backend:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDetections()
  }, [])

  return (
    <Panel
      title="History & Logs (SQLite)"
      icon={<ScrollText className="size-4" />}
      bodyClassName="p-0"
      action={
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadDetections}
            disabled={loading}
            className="flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={`size-3 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <span className="font-mono text-[11px] text-muted-foreground">waste_sorter.db</span>
        </div>
      }
    >
      <div className="max-h-[520px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-card/95 backdrop-blur">
            <tr className="border-b border-border text-left font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="px-4 py-2.5 font-medium">ID</th>
              <th className="px-4 py-2.5 font-medium">Time</th>
              <th className="px-4 py-2.5 font-medium">Category</th>
              <th className="px-4 py-2.5 font-medium">Code</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 text-right font-medium">Conf.</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center font-mono text-xs text-muted-foreground">
                  {loading ? 'Loading detections from SQLite...' : 'No historical detections logged yet.'}
                </td>
              </tr>
            ) : (
              items.map((r) => {
                const catKey = r.category.toUpperCase() as WasteCategory
                const meta = CATEGORY_MAP[catKey] ?? CATEGORY_MAP.PLASTIC
                const hexColor = COLOR_HEX[catKey] ?? '#00f2fe'
                const formattedTime = new Date(r.timestamp).toLocaleTimeString()

                return (
                  <tr key={r.id} className="border-b border-border/50 transition-colors hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">{r.id}</td>
                    <td className="px-4 py-2.5 font-mono text-xs tabular-nums">{formattedTime}</td>
                    <td className="px-4 py-2.5">
                      <span className="inline-flex items-center gap-2 text-xs font-medium">
                        <span className="size-2 rounded-full" style={{ background: hexColor }} />
                        {r.label || meta.label}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="font-mono text-xs font-bold" style={{ color: hexColor }}>
                        [{r.code || meta.code}]
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                      {r.status || 'PROCESSED'}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-emerald">
                      {r.confidence}%
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  )
}
