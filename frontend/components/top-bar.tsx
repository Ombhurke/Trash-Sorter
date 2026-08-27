'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'
import type { OperatingMode, SystemState, Telemetry } from '@/lib/types'
import { STATE_VISUALS } from '@/lib/state-visuals'

export function TopBar({
  telemetry,
  onModeChange,
}: {
  telemetry: Telemetry
  onModeChange: (mode: OperatingMode) => void
}) {
  return (
    <header className="glass sticky top-0 z-20 flex flex-wrap items-center gap-3 rounded-2xl px-4 py-3">
      <ModeToggle mode={telemetry.mode} onChange={onModeChange} />
      <StateBadge state={telemetry.state} progress={telemetry.thinkingProgress} />

      <div className="ml-auto flex items-center gap-3">
        <TelemetryStrip fps={telemetry.fps} hardwareConnected={telemetry.hardwareConnected} serialPort={telemetry.serialPort} />
      </div>
    </header>
  )
}

function ModeToggle({
  mode,
  onChange,
}: {
  mode: OperatingMode
  onChange: (mode: OperatingMode) => void
}) {
  const modes: { key: OperatingMode; label: string }[] = [
    { key: 'AUTONOMOUS', label: 'Autonomous' },
    { key: 'MANUAL', label: 'Manual' },
  ]
  return (
    <div className="flex rounded-xl bg-secondary p-1">
      {modes.map((m) => (
        <button
          key={m.key}
          type="button"
          onClick={() => onChange(m.key)}
          className={cn(
            'rounded-lg px-3 py-1.5 text-xs font-semibold transition-all',
            mode === m.key
              ? 'bg-primary text-primary-foreground shadow-[0_0_16px_-2px_var(--cyan)]'
              : 'text-muted-foreground hover:text-foreground',
          )}
        >
          {m.label}
        </button>
      ))}
    </div>
  )
}

function StateBadge({ state, progress }: { state: SystemState; progress: number }) {
  const v = STATE_VISUALS[state] ?? STATE_VISUALS.WAITING
  return (
    <div
      className={cn(
        'flex items-center gap-2.5 rounded-xl px-3 py-1.5 ring-1 ring-inset',
        v.ring,
      )}
    >
      <span className={cn('size-2.5 rounded-full', v.dot)} />
      <span className={cn('font-mono text-xs font-bold tracking-wider', v.text)}>
        {v.label}
        {state === 'THINKING' && ` (${(5.0 * (progress / 100)).toFixed(1)}s)`}
      </span>
    </div>
  )
}

function TelemetryStrip({ fps, hardwareConnected, serialPort }: { fps: number; hardwareConnected?: boolean; serialPort?: string }) {
  const [now, setNow] = useState<string>('')
  useEffect(() => {
    const tick = () =>
      setNow(
        new Date().toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
      )
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex items-center gap-4 font-mono text-xs text-muted-foreground">
      <span>
        FPS <span className="text-emerald font-bold">{fps.toFixed(1)}</span>
      </span>
      <span className="hidden sm:inline">
        {hardwareConnected ? (
          <span className="text-emerald">● {serialPort ?? 'COM3'} (19200)</span>
        ) : (
          <span className="text-zinc-500">○ No Hardware</span>
        )}
      </span>
      <span className="tabular-nums text-foreground">{now}</span>
    </div>
  )
}
