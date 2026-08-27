'use client'

import { useEffect, useState, useRef } from 'react'
import {
  Gamepad2,
  House,
  RotateCcw,
  Package,
  Newspaper,
  Boxes,
  GlassWater,
  Layers,
  Loader2,
  Send,
  Plug,
  Unplug,
  RefreshCw,
  Terminal,
  Trash2,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Cpu,
  Sparkles,
} from 'lucide-react'
import { Panel } from '@/components/panel'
import { cn } from '@/lib/utils'
import {
  CATEGORIES,
  type ManualCommand,
  type Telemetry,
  type WasteCategory,
  type SerialLogEntry,
} from '@/lib/types'
import { api } from '@/services/api'

const CATEGORY_ICONS: Record<WasteCategory, typeof Package> = {
  PLASTIC: Package,
  PAPER: Newspaper,
  METAL: Boxes,
  GLASS: GlassWater,
  CARDBOARD: Layers,
}

interface PortOption {
  port: string
  description: string
}

export function ManualControlCard({
  telemetry,
  onCommand,
  onConnect,
  onDisconnect,
  onSendRaw,
  onClearLogs,
  disabled,
}: {
  telemetry?: Telemetry
  onCommand: (command: ManualCommand) => void
  onConnect?: (port: string, baudRate?: number) => Promise<any>
  onDisconnect?: () => Promise<any>
  onSendRaw?: (command: string) => Promise<any>
  onClearLogs?: () => Promise<any>
  disabled?: boolean
}) {
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const isOperating = telemetry?.state === 'OPERATING'
  const isEmergency = telemetry?.state === 'EMERGENCY'

  // Serial Port Connection State
  const [portOptions, setPortOptions] = useState<PortOption[]>([
    { port: 'COM3', description: 'Arduino UNO / USB-SERIAL (Default)' },
    { port: 'COM1', description: 'Communications Port (COM1)' },
    { port: 'COM2', description: 'Communications Port (COM2)' },
    { port: 'COM4', description: 'USB Serial Device (COM4)' },
    { port: 'COM5', description: 'USB Serial Device (COM5)' },
  ])
  const [selectedPort, setSelectedPort] = useState<string>('COM3')
  const [customPort, setCustomPort] = useState<string>('')
  const [baudRate, setBaudRate] = useState<number>(19200)
  const [isConnecting, setIsConnecting] = useState<boolean>(false)
  const [isScanning, setIsScanning] = useState<boolean>(false)
  const [autoConnectOnSelect, setAutoConnectOnSelect] = useState<boolean>(true)
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'info' | 'success' | 'error' } | null>(null)

  // Serial Monitor Terminal State
  const [showTerminal, setShowTerminal] = useState<boolean>(true)
  const [rawCommandInput, setRawCommandInput] = useState<string>('')
  const [localLogs, setLocalLogs] = useState<SerialLogEntry[]>([])
  const terminalScrollRef = useRef<HTMLDivElement>(null)
  const [mounted, setMounted] = useState<boolean>(false)
  const isConnected = Boolean(telemetry?.hardwareConnected)
  const activePort = telemetry?.serialPort || selectedPort

  useEffect(() => {
    setMounted(true)
  }, [])

  // Sync available ports from telemetry or load on mount
  useEffect(() => {
    if (telemetry?.availablePortsInfo && telemetry.availablePortsInfo.length > 0) {
      setPortOptions(
        telemetry.availablePortsInfo.map((p) => ({
          port: p.port,
          description: p.description || p.port,
        }))
      )
    } else if (telemetry?.availablePorts && telemetry.availablePorts.length > 0) {
      setPortOptions(
        telemetry.availablePorts.map((p) => ({
          port: p,
          description: p === 'COM3' ? 'Arduino UNO (Default)' : 'Serial Port',
        }))
      )
    }

    if (telemetry?.serialPort) {
      setSelectedPort(telemetry.serialPort)
    }
  }, [telemetry?.availablePortsInfo, telemetry?.availablePorts, telemetry?.serialPort])

  // Sync serial logs from telemetry
  useEffect(() => {
    if (telemetry?.serialLogs && telemetry.serialLogs.length > 0) {
      setLocalLogs(telemetry.serialLogs)
    }
  }, [telemetry?.serialLogs])

  // Auto-scroll terminal on new log
  useEffect(() => {
    if (terminalScrollRef.current) {
      terminalScrollRef.current.scrollTop = terminalScrollRef.current.scrollHeight
    }
  }, [localLogs])

  // Initial port scan on component mount
  useEffect(() => {
    handleScanPorts(false)
  }, [])

  // Clear active action state when operating finishes
  useEffect(() => {
    if (!isOperating) {
      setActiveAction(null)
    }
  }, [isOperating])

  // Scan COM ports function
  const handleScanPorts = async (showToast: boolean = true) => {
    setIsScanning(true)
    try {
      const res = await api.getSerialPorts()
      if (res && res.ports && res.ports.length > 0) {
        const mapped = res.ports.map((p) => ({
          port: p.port,
          description: p.description || 'USB Serial Device',
        }))
        setPortOptions(mapped)
        
        // If current selectedPort is not in detected list, pick the first detected
        if (!mapped.some((p) => p.port === selectedPort) && mapped.length > 0) {
          setSelectedPort(mapped[0].port)
        }

        if (showToast) {
          setStatusMessage({
            text: `Scanned and found ${mapped.length} active hardware port(s): ${mapped.map((p) => p.port).join(', ')}`,
            type: 'info',
          })
        }
      } else {
        if (showToast) {
          setStatusMessage({
            text: 'Scan completed: No active USB devices found. Verify cable is plugged in.',
            type: 'info',
          })
        }
      }
    } catch {
      // Keep existing list
    } finally {
      setIsScanning(false)
      setTimeout(() => setStatusMessage(null), 4500)
    }
  }

  // Connect to Serial Port
  const handleConnect = async (targetPort?: string) => {
    const portToConnect = targetPort || (selectedPort === 'CUSTOM' ? customPort.trim() : selectedPort)
    if (!portToConnect) {
      setStatusMessage({ text: 'Please enter or select a valid COM port name.', type: 'error' })
      return
    }

    setIsConnecting(true)
    setStatusMessage({ text: `Connecting to ${portToConnect} at ${baudRate} Baud...`, type: 'info' })

    try {
      const res = onConnect
        ? await onConnect(portToConnect, baudRate)
        : await api.connectSerial(portToConnect, baudRate)

      if (res && res.connected) {
        setStatusMessage({
          text: `Connected to Arduino UNO on ${portToConnect} @ ${baudRate} Baud! Ready for sorting commands.`,
          type: 'success',
        })
      } else {
        setStatusMessage({
          text: res?.message || `Port ${portToConnect} connection processed.`,
          type: res?.connected ? 'success' : 'info',
        })
      }
    } catch (err: any) {
      setStatusMessage({ text: `Connection failed on ${portToConnect}: ${err?.message || err}`, type: 'error' })
    } finally {
      setIsConnecting(false)
      setTimeout(() => setStatusMessage(null), 5000)
    }
  }

  // Handle Port Selection Change
  const handlePortSelectionChange = (newPort: string) => {
    setSelectedPort(newPort)
    if (newPort !== 'CUSTOM' && autoConnectOnSelect) {
      handleConnect(newPort)
    }
  }

  // Disconnect from Serial Port
  const handleDisconnect = async () => {
    setIsConnecting(true)
    try {
      if (onDisconnect) {
        await onDisconnect()
      } else {
        await api.disconnectSerial()
      }
      setStatusMessage({ text: 'Serial port disconnected.', type: 'info' })
    } catch (err: any) {
      setStatusMessage({ text: `Disconnect error: ${err?.message || err}`, type: 'error' })
    } finally {
      setIsConnecting(false)
      setTimeout(() => setStatusMessage(null), 3000)
    }
  }

  // Global Keyboard hotkeys
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      const key = e.key.toUpperCase()

      const cat = CATEGORIES.find((c) => c.hotkey === key)
      if (cat) {
        handleTrigger(cat.key, cat.code)
        return
      }

      if (key === 'H') handleTrigger('HOME', 'H')
      else if (key === 'R') handleTrigger('RESET', 'R')
      else if (key === 'E') handleTrigger('STOP', 'E')
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onCommand, isOperating])

  const handleTrigger = (action: ManualCommand['action'], code: string) => {
    // Strictly prevent starting multiple simultaneous routines
    if (isOperating) return
    setActiveAction(action)

    // Add immediate local TX entry
    const newEntry: SerialLogEntry = {
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      direction: 'TX',
      data: `'${code}' -> ${action} Throw Routine`,
    }
    setLocalLogs((prev) => [...prev.slice(-99), newEntry])

    onCommand({ action, code })
  }

  const handleSendRaw = async () => {
    const cmd = rawCommandInput.trim().toUpperCase()
    if (!cmd) return

    setRawCommandInput('')
    const newEntry: SerialLogEntry = {
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      direction: 'TX',
      data: `'${cmd}' (Raw Test Command)`,
    }
    setLocalLogs((prev) => [...prev.slice(-99), newEntry])

    try {
      if (onSendRaw) {
        await onSendRaw(cmd)
      } else {
        await api.sendRawSerial(cmd)
      }
    } catch (err) {
      console.error('Failed to send raw command:', err)
    }
  }

  const handleClearLogs = async () => {
    setLocalLogs([])
    try {
      if (onClearLogs) {
        await onClearLogs()
      } else {
        await api.clearSerialLogs()
      }
    } catch {
      // ignore
    }
  }

  if (!mounted) {
    return (
      <Panel
        title="Manual Waste Segregation & USB Serial Control"
        icon={<Gamepad2 className="size-4 text-sky-600" />}
        action={
          <span className="font-mono text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
            19200 Baud · Arduino
          </span>
        }
      >
        <div className="flex h-80 items-center justify-center font-mono text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Loader2 className="size-4 animate-spin text-sky-600" />
            <span>Loading manual segregation controls...</span>
          </div>
        </div>
      </Panel>
    )
  }

  return (
    <Panel
      title="Manual Waste Segregation & USB Serial Control"
      icon={<Gamepad2 className="size-4 text-sky-600" />}
      action={
        <div className="flex items-center gap-2">
          {isOperating ? (
            <span className="flex items-center gap-1.5 rounded-full bg-sky-100 px-3 py-1 font-mono text-xs font-bold text-sky-800 ring-1 ring-sky-300 animate-pulse shadow-xs">
              <Loader2 className="size-3.5 animate-spin text-sky-600" />
              <span>ARM SORTING...</span>
            </span>
          ) : isConnected ? (
            <span className="flex items-center gap-1.5 font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
              <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
              {activePort} · 19200 Baud
            </span>
          ) : (
            <span className="flex items-center gap-1.5 font-mono text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200">
              <span className="size-2 rounded-full bg-amber-500" />
              Serial Standby
            </span>
          )}
        </div>
      }
    >
      {/* 1. USB COM Port Selection & Connect Bar */}
      <div className="mb-4 rounded-xl border border-slate-200 bg-slate-50/90 p-3.5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-200/80">
          <div className="flex items-center gap-2">
            <Plug className="size-4 text-sky-600" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Arduino USB COM Connection:
            </span>
            {portOptions.length > 0 && (
              <span className="font-mono text-[10px] font-bold text-sky-700 bg-sky-100 px-1.5 py-0.2 rounded">
                {portOptions.length} Ports Found
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              suppressHydrationWarning
              onClick={() => handleScanPorts(true)}
              disabled={isScanning || isConnecting}
              title="Rescan available hardware COM ports"
              className="flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100 hover:text-sky-600 transition-colors shadow-2xs"
            >
              <RefreshCw className={cn('size-3', isScanning && 'animate-spin text-sky-600')} />
              <span>{isScanning ? 'Scanning...' : 'Scan Ports'}</span>
            </button>

            <span className="font-mono text-[11px] font-bold text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
              19200 Baud
            </span>
          </div>
        </div>

        {/* COM Port Selector + Connect/Disconnect Actions */}
        <div className="mt-2.5 flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <div className="flex-1 flex items-center gap-2 min-w-0">
            <select
              value={selectedPort}
              suppressHydrationWarning
              onChange={(e) => handlePortSelectionChange(e.target.value)}
              disabled={isConnecting}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-xs font-bold text-slate-800 shadow-2xs outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 truncate"
            >
              {portOptions.map((p) => (
                <option key={p.port} value={p.port}>
                  {p.port} — {p.description}
                </option>
              ))}
              <option value="CUSTOM">+ Enter Custom COM Port...</option>
            </select>

            {selectedPort === 'CUSTOM' && (
              <input
                type="text"
                suppressHydrationWarning
                placeholder="e.g. COM7"
                value={customPort}
                onChange={(e) => setCustomPort(e.target.value)}
                className="w-28 rounded-lg border border-slate-300 bg-white px-2.5 py-2 font-mono text-xs text-slate-900 outline-none focus:border-sky-500"
              />
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {isConnected ? (
              <button
                type="button"
                suppressHydrationWarning
                onClick={handleDisconnect}
                disabled={isConnecting}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2 font-mono text-xs font-bold text-rose-700 hover:bg-rose-100 hover:border-rose-300 transition-all shadow-xs"
              >
                {isConnecting ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <Unplug className="size-3.5 text-rose-600" />
                )}
                <span>Disconnect</span>
              </button>
            ) : (
              <button
                type="button"
                suppressHydrationWarning
                onClick={() => handleConnect()}
                disabled={isConnecting}
                className="flex items-center justify-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 font-mono text-xs font-bold text-white hover:bg-sky-700 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-xs"
              >
                {isConnecting ? (
                  <Loader2 className="size-3.5 animate-spin text-white" />
                ) : (
                  <Plug className="size-3.5 text-white" />
                )}
                <span>Connect Arduino</span>
              </button>
            )}
          </div>
        </div>

        {/* Feedback Message */}
        {statusMessage && (
          <div
            className={cn(
              'mt-2.5 flex items-center gap-2 rounded-lg p-2.5 text-xs font-medium transition-all shadow-2xs',
              statusMessage.type === 'success' && 'bg-emerald-100 text-emerald-900 border border-emerald-300',
              statusMessage.type === 'info' && 'bg-sky-100 text-sky-900 border border-sky-300',
              statusMessage.type === 'error' && 'bg-rose-100 text-rose-900 border border-rose-300'
            )}
          >
            {statusMessage.type === 'success' ? (
              <CheckCircle2 className="size-4 shrink-0 text-emerald-600" />
            ) : statusMessage.type === 'error' ? (
              <AlertCircle className="size-4 shrink-0 text-rose-600" />
            ) : (
              <Plug className="size-4 shrink-0 text-sky-600" />
            )}
            <span className="flex-1 font-mono text-[11px] font-semibold leading-tight">{statusMessage.text}</span>
          </div>
        )}
      </div>

      {/* 2. Waste Segregation Triggers */}
      <div className="mb-2 flex items-center justify-between border-b border-slate-100 pb-2">
        <p className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Select Trash Category To Send Serial Signal:
        </p>
        <span className="font-mono text-[11px] font-bold text-sky-600">
          Direct 6-DOF Throw
        </span>
      </div>

      {/* Clean Category Rows */}
      <div className="flex flex-col gap-2">
        {CATEGORIES.map((c) => {
          const Icon = CATEGORY_ICONS[c.key]
          const isCurrentActive = ((activeAction === c.key) || (telemetry?.lastDetection?.category === c.key)) && isOperating

          return (
            <button
              key={c.key}
              type="button"
              disabled={disabled || isOperating}
              onClick={() => handleTrigger(c.key, c.code)}
              className={cn(
                'group relative flex items-center justify-between rounded-xl border p-2.5 text-left transition-all duration-150 shadow-xs',
                isCurrentActive
                  ? 'border-sky-500 bg-sky-50/90 ring-2 ring-sky-400 shadow-md scale-[0.99]'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/90 hover:shadow-sm hover:-translate-y-0.5 active:translate-y-0',
                'disabled:pointer-events-none disabled:opacity-40'
              )}
            >
              {/* Left: Icon + Label + Bin Destination */}
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className="grid size-9 shrink-0 place-items-center rounded-xl font-bold shadow-2xs"
                  style={{
                    background: `${c.color}18`,
                    color: c.color,
                    border: `1.5px solid ${c.color}35`,
                  }}
                >
                  <Icon className="size-4.5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900 tracking-tight truncate">
                      {c.label}
                    </span>
                    <span
                      className="font-mono text-xs font-black px-1.5 py-0.2 rounded shrink-0 border"
                      style={{
                        color: c.color,
                        background: `${c.color}15`,
                        borderColor: `${c.color}40`,
                      }}
                    >
                      [{c.code}]
                    </span>
                  </div>
                  <span className="text-[11px] font-mono font-semibold text-slate-500 mt-0.5 block truncate">
                    ➔ {c.bin}
                  </span>
                </div>
              </div>

              {/* Right: Hotkey & Action Button */}
              <div className="flex items-center gap-2 shrink-0 ml-3">
                <kbd
                  className="font-mono text-xs font-extrabold px-2 py-1 rounded-md shadow-2xs text-white"
                  style={{ background: c.color }}
                >
                  {c.hotkey}
                </kbd>

                <div
                  className={cn(
                    'flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-mono text-xs font-bold transition-all shadow-xs',
                    isCurrentActive
                      ? 'bg-sky-600 text-white animate-pulse'
                      : 'bg-slate-100 text-slate-700 group-hover:bg-sky-600 group-hover:text-white'
                  )}
                >
                  {isCurrentActive ? (
                    <>
                      <Loader2 className="size-3.5 animate-spin" />
                      <span>Sorting</span>
                    </>
                  ) : (
                    <>
                      <span>Throw</span>
                      <Send className="size-3 transition-transform group-hover:translate-x-0.5" />
                    </>
                  )}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* 3. Calibration & Safety Controls */}
      <div className="mt-3.5 border-t border-slate-100 pt-3">
        <p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
          Calibration & Safety Controls:
        </p>
        <div className="grid grid-cols-3 gap-2">
          <UtilBtn
            label="Home (90°)"
            hotkey="H"
            icon={<House className="size-3.5 text-sky-600" />}
            onClick={() => handleTrigger('HOME', 'H')}
            disabled={disabled || isOperating}
          />
          <UtilBtn
            label="Reset Arm"
            hotkey="R"
            icon={<RotateCcw className="size-3.5 text-emerald-600" />}
            onClick={() => handleTrigger('RESET', 'R')}
            disabled={disabled || isOperating}
          />
          <UtilBtn
            label="E-Stop"
            hotkey="E"
            variant="danger"
            icon={<ShieldAlert className="size-3.5 text-rose-600" />}
            onClick={() => handleTrigger('STOP', 'E')}
            disabled={disabled}
          />
        </div>
      </div>

      {/* 4. Live Serial Monitor Terminal */}
      <div className="mt-4 border-t border-slate-200 pt-3">
        <div className="flex items-center justify-between mb-2">
          <button
            type="button"
            onClick={() => setShowTerminal(!showTerminal)}
            className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-700 hover:text-sky-600 transition-colors"
          >
            <Terminal className="size-3.5 text-sky-600" />
            <span>Live Arduino Serial Monitor</span>
            {showTerminal ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
          </button>

          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-slate-400">
              {localLogs.length} messages
            </span>
            <button
              type="button"
              onClick={handleClearLogs}
              className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 hover:text-rose-600 transition-colors"
            >
              <Trash2 className="size-3" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {showTerminal && (
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-white shadow-inner font-mono">
            {/* Terminal Log Console */}
            <div
              ref={terminalScrollRef}
              className="h-36 overflow-y-auto space-y-1 text-xs pr-1 scrollbar-thin scrollbar-thumb-slate-700"
            >
              {localLogs.length === 0 ? (
                <div className="text-slate-500 italic py-4 text-center">
                  Serial monitor ready · Select COM port & click any trash button to transmit signals.
                </div>
              ) : (
                localLogs.map((log, idx) => {
                  const isTX = log.direction.includes('TX')
                  const isRX = log.direction.includes('RX')
                  const isErr = log.direction.includes('ERROR')

                  return (
                    <div key={idx} className="flex items-start gap-2 leading-relaxed break-all">
                      <span className="text-slate-500 text-[10px] shrink-0">{log.timestamp}</span>
                      <span
                        className={cn(
                          'text-[10px] font-bold px-1 rounded shrink-0',
                          isTX && 'bg-sky-900/80 text-sky-300 border border-sky-700',
                          isRX && 'bg-emerald-900/80 text-emerald-300 border border-emerald-700',
                          isErr && 'bg-rose-900/80 text-rose-300 border border-rose-700',
                          !isTX && !isRX && !isErr && 'bg-purple-900/80 text-purple-300 border border-purple-700'
                        )}
                      >
                        {log.direction}
                      </span>
                      <span
                        className={cn(
                          'text-slate-200',
                          isTX && 'text-sky-200',
                          isRX && 'text-emerald-200 font-semibold',
                          isErr && 'text-rose-300'
                        )}
                      >
                        {log.data}
                      </span>
                    </div>
                  )
                })
              )}
            </div>

            {/* Quick Test Bar & Raw Serial Input */}
            <div className="mt-2.5 pt-2 border-t border-slate-800 flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
                <span className="text-[10px] text-slate-400 font-bold uppercase shrink-0">Quick Test:</span>
                {['P', 'M', 'C', 'A', 'G', 'H'].map((char) => (
                  <button
                    key={char}
                    type="button"
                    onClick={() => {
                      setRawCommandInput(char)
                      handleTrigger(
                        char === 'P'
                          ? 'PLASTIC'
                          : char === 'M'
                          ? 'METAL'
                          : char === 'C'
                          ? 'CARDBOARD'
                          : char === 'A'
                          ? 'PAPER'
                          : char === 'G'
                          ? 'GLASS'
                          : 'HOME',
                        char
                      )
                    }}
                    className="rounded bg-slate-800 hover:bg-sky-600 hover:text-white px-2 py-0.5 text-[11px] font-bold text-slate-300 border border-slate-700 transition-colors"
                  >
                    [{char}]
                  </button>
                ))}
              </div>

              <div className="flex-1 flex items-center gap-1.5 min-w-0">
                <input
                  type="text"
                  placeholder="Send raw character (e.g. P)..."
                  value={rawCommandInput}
                  onChange={(e) => setRawCommandInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendRaw()}
                  className="flex-1 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-1 text-xs text-white placeholder-slate-500 outline-none focus:border-sky-500"
                />
                <button
                  type="button"
                  onClick={handleSendRaw}
                  className="rounded-lg bg-sky-600 px-3 py-1 text-xs font-bold text-white hover:bg-sky-700 transition-colors shadow-2xs"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Panel>
  )
}

function UtilBtn({
  label,
  hotkey,
  icon,
  onClick,
  disabled,
  variant = 'default',
}: {
  label: string
  hotkey: string
  icon: React.ReactNode
  onClick: () => void
  disabled?: boolean
  variant?: 'default' | 'danger'
}) {
  return (
    <button
      type="button"
      suppressHydrationWarning
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex items-center justify-between rounded-xl border px-2.5 py-2 text-xs font-bold shadow-2xs transition-all duration-150',
        variant === 'danger'
          ? 'border-rose-200 bg-rose-50/60 text-rose-800 hover:bg-rose-100 hover:border-rose-300'
          : 'border-slate-200 bg-white text-slate-800 hover:border-slate-300 hover:bg-slate-50',
        'hover:-translate-y-0.5 active:translate-y-0',
        'disabled:pointer-events-none disabled:opacity-40'
      )}
    >
      <div className="flex items-center gap-1.5 min-w-0">
        {icon}
        <span className="text-[11px] font-semibold truncate">{label}</span>
      </div>
      <kbd
        className={cn(
          'font-mono text-[10px] font-bold px-1.5 py-0.2 rounded border',
          variant === 'danger'
            ? 'bg-rose-100 text-rose-700 border-rose-200'
            : 'bg-slate-100 text-slate-500 border-slate-200'
        )}
      >
        [{hotkey}]
      </kbd>
    </button>
  )
}
