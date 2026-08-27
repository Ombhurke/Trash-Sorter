'use client'

import { useState, useRef } from 'react'
import {
  Camera,
  Maximize2,
  Play,
  Square,
  RefreshCw,
  ScanLine,
  CheckCircle2,
  Power,
  Sparkles,
} from 'lucide-react'
import { Panel } from '@/components/panel'
import { cn } from '@/lib/utils'
import type { Telemetry } from '@/lib/types'
import { CATEGORY_MAP } from '@/lib/types'
import { api, VIDEO_FEED_URL } from '@/services/api'

export function LiveCameraCard({
  telemetry,
  onToggleDetection,
}: {
  telemetry: Telemetry
  onToggleDetection?: () => void
}) {
  // Starts OFF by default on load: Camera will NOT turn on until user clicks "Turn On Cam"
  const [cameraEnabled, setCameraEnabled] = useState(false)
  const [hud, setHud] = useState(true)
  const [streamError, setStreamError] = useState(false)
  const [streamKey, setStreamKey] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  const det = telemetry.lastDetection
  const meta = CATEGORY_MAP[det.category] ?? CATEGORY_MAP.PLASTIC
  const isDetectionActive = (telemetry.detectionActive ?? false) && cameraEnabled
  const isThinking = telemetry.state === 'THINKING'
  const isOperating = telemetry.state === 'OPERATING'

  const handleToggleCamera = async () => {
    const nextState = !cameraEnabled
    setCameraEnabled(nextState)
    if (nextState) {
      setStreamError(false)
      setStreamKey((prev) => prev + 1)
      try {
        await api.startDetection()
      } catch (err) {
        console.error('Failed to start camera hardware:', err)
      }
    } else {
      try {
        await api.stopDetection()
      } catch (err) {
        console.error('Failed to release camera hardware:', err)
      }
    }
    if (onToggleDetection) {
      onToggleDetection()
    }
  }

  const handleRetryStream = () => {
    setStreamError(false)
    setStreamKey((prev) => prev + 1)
  }

  const toggleFullscreen = () => {
    if (!containerRef.current) return
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }

  return (
    <Panel
      title="Live Camera Feed & Autonomous Trash Sorter"
      icon={<Camera className="size-4 text-sky-600" />}
      className="row-span-2"
      bodyClassName="p-3"
      action={
        <div className="flex items-center gap-2">
          {/* Main Turn On / Turn Off Camera & Detection Button */}
          <button
            type="button"
            onClick={handleToggleCamera}
            className={cn(
              'flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold shadow-xs transition-all duration-200',
              cameraEnabled && isDetectionActive
                ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-300 hover:bg-rose-50 hover:text-rose-700 hover:ring-rose-300'
                : 'bg-sky-600 text-white hover:bg-sky-700 shadow-md animate-pulse'
            )}
          >
            {cameraEnabled && isDetectionActive ? (
              <>
                <span className="relative flex size-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
                </span>
                <Square className="size-3 fill-current" />
                <span>TURN OFF CAM</span>
              </>
            ) : (
              <>
                <Play className="size-3.5 fill-white" />
                <span>TURN ON CAM & DETECT</span>
              </>
            )}
          </button>

          <HudToggle on={hud} onClick={() => setHud((v) => !v)} />

          <button
            type="button"
            aria-label="Fullscreen"
            onClick={toggleFullscreen}
            className="grid size-7 place-items-center rounded-lg bg-slate-100 text-slate-600 transition-colors hover:text-slate-900"
          >
            <Maximize2 className="size-3.5" />
          </button>
        </div>
      }
    >
      <div
        ref={containerRef}
        className="relative aspect-video w-full overflow-hidden rounded-xl bg-slate-950 ring-1 ring-border shadow-inner"
      >
        {cameraEnabled ? (
          !streamError ? (
            /* Single Real-Time Live MJPEG Stream */
            <img
              key={streamKey}
              src={`${VIDEO_FEED_URL}?t=${streamKey}`}
              alt="Live Camera Video Stream"
              className="h-full w-full object-cover select-none"
              onError={() => setStreamError(true)}
            />
          ) : (
            /* Error & Retry Fallback */
            <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-slate-950 p-6 text-center text-slate-400">
              <div className="grid size-12 place-items-center rounded-2xl bg-slate-900 ring-1 ring-white/10">
                <Camera className="size-6 text-slate-500" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-200">Connecting to Camera Stream...</p>
                <p className="font-mono text-xs text-slate-500 mt-0.5">{VIDEO_FEED_URL}</p>
              </div>
              <button
                type="button"
                onClick={handleRetryStream}
                className="mt-1 flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-700"
              >
                <RefreshCw className="size-3.5" />
                <span>Reconnect Camera</span>
              </button>
            </div>
          )
        ) : (
          /* Camera Standby Screen (Default on Load) */
          <div className="flex h-full w-full flex-col items-center justify-center gap-4 bg-gradient-to-b from-slate-900 via-slate-950 to-black p-6 text-center">
            <div className="grid size-16 place-items-center rounded-2xl bg-slate-800/90 ring-1 ring-white/10 shadow-lg">
              <Power className="size-8 text-sky-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Camera in Standby Mode</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md leading-relaxed">
                The video camera and AI detector are currently paused. Click below to turn on the camera and begin autonomous sorting.
              </p>
            </div>
            <button
              type="button"
              onClick={handleToggleCamera}
              className="flex items-center gap-2 rounded-xl bg-sky-600 px-6 py-3 text-xs font-bold text-white shadow-lg shadow-sky-500/30 transition-all hover:bg-sky-500 hover:scale-105 active:scale-95"
            >
              <Play className="size-4 fill-white" />
              <span>TURN ON CAMERA & DETECT</span>
            </button>
          </div>
        )}

        {/* Top-Left Live Status Badge */}
        {cameraEnabled && (
          <div className="absolute left-3 top-3 flex items-center gap-2 rounded-md bg-black/70 px-2.5 py-1 font-mono text-[11px] backdrop-blur-md ring-1 ring-white/10 z-10">
            <span
              className={cn(
                'size-2 rounded-full',
                isOperating
                  ? 'bg-sky-400 animate-pulse'
                  : isThinking
                  ? 'bg-amber-400 animate-ping'
                  : isDetectionActive
                  ? 'bg-emerald-400 animate-status-blink shadow-[0_0_8px_#10b981]'
                  : 'bg-slate-500'
              )}
            />
            <span className="font-bold tracking-wider text-white">
              {isOperating
                ? 'ARM THROWING'
                : isThinking
                ? `IDENTIFYING TRASH (5s)`
                : isDetectionActive
                ? 'CAM LIVE · WAITING FOR TRASH'
                : 'STANDBY'}
            </span>
          </div>
        )}

        {/* Top-Right FPS Counter */}
        {cameraEnabled && (
          <div className="absolute right-3 top-3 rounded-md bg-black/70 px-2.5 py-1 font-mono text-[11px] tracking-wider text-sky-400 backdrop-blur-md ring-1 ring-white/10 z-10">
            {telemetry.fps.toFixed(1)} FPS
          </div>
        )}

        {/* Floating Bottom Detection & Throw Bar */}
        {cameraEnabled && hud && (
          <div className="absolute bottom-3 inset-x-3 flex items-center justify-between pointer-events-none z-10">
            <div
              className="flex items-center gap-2 rounded-lg bg-black/80 px-3 py-1.5 font-mono text-xs font-bold backdrop-blur-md ring-1 ring-white/10"
              style={{ borderColor: `${meta.color}60` }}
            >
              <span className="size-2 rounded-full" style={{ background: meta.color }} />
              <span className="text-white">{meta.label.toUpperCase()}</span>
              <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] text-sky-300">
                [{det.code}]
              </span>
              <span className="text-slate-400">·</span>
              <span style={{ color: meta.color }}>{det.confidence.toFixed(1)}%</span>
              <span className="text-[11px] text-slate-300 font-normal">➔ {meta.bin}</span>
            </div>

            {isOperating ? (
              <div className="flex items-center gap-1.5 rounded-lg bg-sky-500/20 px-3 py-1.5 font-mono text-xs font-bold text-sky-300 backdrop-blur-md ring-1 ring-sky-400/50 animate-pulse">
                <CheckCircle2 className="size-3.5 text-sky-400" />
                <span>THROWING: {meta.label.toUpperCase()}</span>
              </div>
            ) : isThinking ? (
              <div className="flex items-center gap-1.5 rounded-lg bg-amber-500/20 px-3 py-1.5 font-mono text-xs font-bold text-amber-300 backdrop-blur-md ring-1 ring-amber-400/50">
                <span className="size-2 rounded-full bg-amber-400 animate-ping" />
                <span>SAMPLING (5s Consensus: {telemetry.thinkingProgress}%)</span>
              </div>
            ) : null}
          </div>
        )}
      </div>

      <div className="mt-2.5 flex items-center justify-between px-1 font-mono text-[11px] text-slate-500">
        <span>YOLOv8 Engine · 1280×720 @ 64 FPS</span>
        <span>
          mode: {telemetry.mode} · 5s cycle · Camera:{' '}
          {cameraEnabled && isDetectionActive ? 'ACTIVE' : 'STANDBY (OFF)'}
        </span>
      </div>
    </Panel>
  )
}

function HudToggle({ on, onClick }: { on: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors',
        on ? 'bg-sky-50 text-sky-700 border border-sky-200' : 'bg-slate-100 text-slate-600 hover:text-slate-900'
      )}
    >
      <ScanLine className="size-3.5" />
      HUD
    </button>
  )
}
