'use client'

import { useState } from 'react'
import { Sidebar, type TabKey } from '@/components/sidebar'
import { TopBar } from '@/components/top-bar'
import { LiveCameraCard } from '@/components/cards/live-camera'
import { LastDetectionCard } from '@/components/cards/last-detection'
import { StatisticsCard } from '@/components/cards/statistics-chart'
import { SystemHealthCard } from '@/components/cards/system-health'
import { ManualControlCard } from '@/components/cards/manual-control'
import { ArmTelemetryCard } from '@/components/cards/arm-telemetry'
import { ThroughputChart } from '@/components/cards/throughput-chart'
import { HistoryLog } from '@/components/cards/history-log'
import { SettingsView } from '@/components/cards/settings-view'
import { Panel } from '@/components/panel'
import { useTelemetry } from '@/lib/use-telemetry'
import { CATEGORIES } from '@/lib/types'

const TAB_TITLES: Record<TabKey, string> = {
  dashboard: 'Dashboard Overview',
  camera: 'Live Camera',
  manual: 'Manual Control',
  stats: 'Statistics & Analytics',
  history: 'History & Logs',
  system: 'System Status',
  settings: 'Settings',
}

export function DashboardShell() {
  const [tab, setTab] = useState<TabKey>('dashboard')
  const {
    data,
    setMode,
    toggleDetection,
    sendCommand,
    connectSerial,
    disconnectSerial,
    sendRawSerial,
    clearSerialLogs,
  } = useTelemetry()

  return (
    <div className="flex min-h-dvh">
      <Sidebar active={tab} onChange={setTab} telemetry={data} />

      <main className="flex min-w-0 flex-1 flex-col gap-4 p-4">
        <TopBar telemetry={data} onModeChange={setMode} />

        <div className="flex items-end justify-between px-1">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-primary">Veg QX</p>
            <h1 className="text-xl font-semibold tracking-tight text-balance">{TAB_TITLES[tab]}</h1>
          </div>
        </div>

        {tab === 'dashboard' && (
          <div className="grid gap-4 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <LiveCameraCard telemetry={data} onToggleDetection={toggleDetection} />
            </div>
            <LastDetectionCard telemetry={data} />
            <StatisticsCard telemetry={data} />
            <SystemHealthCard telemetry={data} />
            <ManualControlCard
              telemetry={data}
              onCommand={sendCommand}
              onConnect={connectSerial}
              onDisconnect={disconnectSerial}
              onSendRaw={sendRawSerial}
              onClearLogs={clearSerialLogs}
            />
            <div className="xl:col-span-2">
              <ArmTelemetryCard telemetry={data} />
            </div>
          </div>
        )}

        {tab === 'camera' && (
          <div className="grid gap-4 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <LiveCameraCard telemetry={data} onToggleDetection={toggleDetection} />
            </div>
            <div className="flex flex-col gap-4">
              <LastDetectionCard telemetry={data} />
              <ArmTelemetryCard telemetry={data} />
            </div>
          </div>
        )}

        {tab === 'manual' && (
          <div className="grid gap-4 lg:grid-cols-2">
            <ManualControlCard
              telemetry={data}
              onCommand={sendCommand}
              onConnect={connectSerial}
              onDisconnect={disconnectSerial}
              onSendRaw={sendRawSerial}
              onClearLogs={clearSerialLogs}
            />
            <ArmTelemetryCard telemetry={data} />
            <LastDetectionCard telemetry={data} />
            <SystemHealthCard telemetry={data} />
          </div>
        )}

        {tab === 'stats' && (
          <div className="flex flex-col gap-4">
            <StatTiles data={data} />
            <div className="grid gap-4 lg:grid-cols-2">
              <ThroughputChart telemetry={data} />
              <StatisticsCard telemetry={data} />
            </div>
          </div>
        )}

        {tab === 'history' && <HistoryLog />}

        {tab === 'system' && (
          <div className="grid gap-4 lg:grid-cols-2">
            <SystemHealthCard telemetry={data} />
            <ArmTelemetryCard telemetry={data} />
            <Panel title="Real-Time Diagnostics & Connection Info" className="lg:col-span-2">
              <div className="grid gap-3 font-mono text-sm sm:grid-cols-3">
                <InfoRow label="Backend API" value="http://localhost:8000" ok={data.connected} />
                <InfoRow label="WebSocket Feed" value={data.wsActive ? "Connected (Live)" : "Disconnected"} ok={data.wsActive} />
                <InfoRow
                  label="Serial Hardware"
                  value={data.hardwareConnected ? `${data.serialPort ?? 'COM3'} · 19200 Baud` : "Arduino Disconnected"}
                  ok={data.hardwareConnected}
                />
                <InfoRow label="System Uptime" value={data.uptime ?? "00:00:01"} ok={data.connected} />
                <InfoRow label="AI Vision Model" value={data.modelName ?? "YOLOv8n Prebuilt"} ok={data.connected} />
                <InfoRow label="Detection Cycle" value="5.0s Consensus" ok={data.connected} />
              </div>
            </Panel>
          </div>
        )}

        {tab === 'settings' && <SettingsView />}
      </main>
    </div>
  )
}

function StatTiles({ data }: { data: ReturnType<typeof useTelemetry>['data'] }) {
  const total = CATEGORIES.reduce((s, c) => s + (data.counts[c.key] ?? 0), 0)
  const tiles = [
    { label: 'Total Items Sorted', value: String(total), accent: '#0284c7' },
    { label: 'AI Sorter Confidence', value: `${data.lastDetection.confidence.toFixed(1)}%`, accent: '#059669' },
    { label: 'Detection Sampling', value: '5.0s Cycle', accent: '#d97706' },
    { label: 'System Uptime', value: data.uptime ?? '00:00:01', accent: '#7c3aed' },
  ]
  return (
    <div className="grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
      {tiles.map((t) => (
        <div key={t.label} className="glass rounded-2xl p-4 border border-slate-200 shadow-xs">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{t.label}</p>
          <p
            className="mt-1 font-mono text-2xl font-black tabular-nums tracking-tight"
            style={{ color: t.accent }}
          >
            {t.value}
          </p>
          <div className="mt-3 h-1.5 rounded-full bg-slate-100 border border-slate-200 overflow-hidden">
            <div className="h-full rounded-full" style={{ width: '75%', background: t.accent }} />
          </div>
        </div>
      ))}
    </div>
  )
}

function InfoRow({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl bg-white p-3.5 border border-slate-200 shadow-xs">
      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
      <span className="flex items-center gap-2 font-bold text-sm text-slate-900 font-mono">
        {ok && <span className="size-2 rounded-full bg-emerald-500 shadow-xs" />}
        {value}
      </span>
    </div>
  )
}
