'use client'

import { useState, useEffect } from 'react'
import {
  Cpu,
  Settings2,
  SlidersHorizontal,
  RefreshCw,
  CheckCircle2,
  Save,
} from 'lucide-react'
import { Panel } from '@/components/panel'
import { cn } from '@/lib/utils'
import { api } from '@/services/api'

export function SettingsView() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [scanningPorts, setScanningPorts] = useState(false)

  // Settings State
  const [availablePorts, setAvailablePorts] = useState<string[]>(['COM1', 'COM2', 'COM3', 'COM4'])
  const [serialPort, setSerialPort] = useState('COM3')
  const [customPort, setCustomPort] = useState('')
  const [baudRate, setBaudRate] = useState(19200)
  const [cameraDevice, setCameraDevice] = useState(0)
  const [resolution, setResolution] = useState('1280 × 720')
  const [apiBase, setApiBase] = useState('http://localhost:8000')

  // Detection Tuning State
  const [confidenceThreshold, setConfidenceThreshold] = useState(40)
  const [thinkingDuration, setThinkingDuration] = useState(5.0)
  const [roiSize, setRoiSize] = useState(50)

  // Behavior Toggles
  const [autoStart, setAutoStart] = useState(true)
  const [logDetections, setLogDetections] = useState(true)
  const [playSound, setPlaySound] = useState(false)
  const [returnToHome, setReturnToHome] = useState(true)

  // Load active settings from backend on mount
  useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true)
        const data = await api.getSettings()
        if (data) {
          if (data.available_ports && data.available_ports.length > 0) {
            setAvailablePorts(data.available_ports)
          }
          if (data.serial_port) setSerialPort(data.serial_port)
          if (data.baud_rate) setBaudRate(data.baud_rate)
          if (typeof data.confidence_threshold === 'number') {
            setConfidenceThreshold(data.confidence_threshold)
          }
          if (typeof data.thinking_duration === 'number') {
            setThinkingDuration(data.thinking_duration)
          }
          if (typeof data.roi_size === 'number') setRoiSize(data.roi_size)
          if (typeof data.camera_device === 'number') setCameraDevice(data.camera_device)
          if (data.resolution) setResolution(data.resolution)
          if (data.api_base) setApiBase(data.api_base)
          if (typeof data.auto_start === 'boolean') setAutoStart(data.auto_start)
          if (typeof data.log_detections === 'boolean') setLogDetections(data.log_detections)
          if (typeof data.return_to_home === 'boolean') setReturnToHome(data.return_to_home)
        }
      } catch (err) {
        console.error('Failed to load settings:', err)
      } finally {
        setLoading(false)
      }
    }
    loadSettings()
  }, [])

  const handleScanPorts = async () => {
    setScanningPorts(true)
    try {
      const portObjs = await api.getSerialPorts()
      const scanned = portObjs.map((p) => p.port)
      if (scanned.length > 0) {
        setAvailablePorts(scanned)
        if (!scanned.includes(serialPort)) {
          setSerialPort(scanned[0])
        }
      } else {
        setAvailablePorts(['COM1', 'COM2', 'COM3', 'COM4', 'COM5'])
      }
    } catch (err) {
      console.error('Error scanning serial ports:', err)
    } finally {
      setScanningPorts(false)
    }
  }

  const handleSaveSettings = async () => {
    setSaving(true)
    setSaveSuccess(false)
    const effectivePort = serialPort === 'CUSTOM' ? customPort : serialPort
    try {
      await api.updateSettings({
        serial_port: effectivePort,
        baud_rate: baudRate,
        confidence_threshold: confidenceThreshold,
        thinking_duration: thinkingDuration,
        roi_size: roiSize,
        camera_device: cameraDevice,
        auto_start: autoStart,
        log_detections: logDetections,
        return_to_home: returnToHome,
      })
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      console.error('Failed to save settings:', err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* 1. Serial Port & Camera Configuration */}
      <Panel
        title="Hardware, Serial & Camera Configuration"
        icon={<Cpu className="size-4 text-sky-600" />}
        action={
          <button
            type="button"
            onClick={handleScanPorts}
            disabled={scanningPorts}
            className="flex items-center gap-1.5 rounded-lg bg-white px-2.5 py-1 font-mono text-xs font-semibold text-sky-700 border border-slate-300 hover:bg-slate-50 transition-colors shadow-xs"
          >
            <RefreshCw className={cn('size-3', scanningPorts && 'animate-spin')} />
            <span>Scan COM Ports</span>
          </button>
        }
      >
        <div className="flex flex-col gap-4">
          {/* Dynamic COM Port Selection */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Arduino Serial Port (COM)
              </label>
              <span className="font-mono text-[11px] text-sky-600 font-bold">
                {availablePorts.length} Ports Detected
              </span>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={serialPort}
                onChange={(e) => setSerialPort(e.target.value)}
                className="flex-1 rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 font-mono text-sm font-bold text-slate-900 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              >
                {availablePorts.map((p) => (
                  <option key={p} value={p}>
                    {p} (Auto-Detected Device)
                  </option>
                ))}
                <option value="CUSTOM">+ Enter Custom COM Port...</option>
              </select>
            </div>
            {serialPort === 'CUSTOM' && (
              <input
                type="text"
                placeholder="e.g. COM7 or /dev/ttyUSB0"
                value={customPort}
                onChange={(e) => setCustomPort(e.target.value)}
                className="mt-1 rounded-xl border border-slate-300 bg-white px-3.5 py-2 font-mono text-sm text-slate-900 outline-none focus:border-sky-500"
              />
            )}
          </div>

          {/* Baud Rate Selection */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Serial Baud Rate
            </label>
            <select
              value={baudRate}
              onChange={(e) => setBaudRate(Number(e.target.value))}
              className="rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 font-mono text-sm font-bold text-slate-900 outline-none focus:border-sky-500"
            >
              <option value={9600}>9600 Baud</option>
              <option value={19200}>19200 Baud (Firmware Recommended)</option>
              <option value={38400}>38400 Baud</option>
              <option value={57600}>57600 Baud</option>
              <option value={115200}>115200 Baud</option>
            </select>
          </div>

          {/* Camera Device Selector */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Camera Device Stream
            </label>
            <select
              value={cameraDevice}
              onChange={(e) => setCameraDevice(Number(e.target.value))}
              className="rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 font-mono text-sm font-bold text-slate-900 outline-none focus:border-sky-500"
            >
              <option value={0}>Camera Index 0 (Primary / Integrated Webcam)</option>
              <option value={1}>Camera Index 1 (External USB Camera)</option>
              <option value={2}>Camera Index 2 (Secondary USB Camera)</option>
            </select>
          </div>

          {/* Resolution & API Base */}
          <div className="grid grid-cols-2 gap-3 pt-1 border-t border-slate-100 text-xs font-mono">
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-200">
              <span className="text-slate-500 block text-[10px] uppercase">Resolution</span>
              <span className="text-slate-900 font-bold text-sm">1280 × 720 @ 64 FPS</span>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-200">
              <span className="text-slate-500 block text-[10px] uppercase">API Endpoint</span>
              <span className="text-sky-600 font-bold text-sm">http://localhost:8000</span>
            </div>
          </div>
        </div>
      </Panel>

      {/* 2. Dynamic Detection Tuning */}
      <Panel
        title="YOLO AI Detection & Timing Tuning"
        icon={<SlidersHorizontal className="size-4 text-amber-600" />}
      >
        <div className="flex flex-col gap-6">
          {/* Confidence Threshold Slider */}
          <DynamicSlider
            label="YOLO Confidence Threshold"
            value={confidenceThreshold}
            min={20}
            max={95}
            step={1}
            unit="%"
            hint={`${confidenceThreshold}% Minimum Certainty`}
            description="Minimum confidence score required for YOLO to trigger item identification."
            color="#0284c7"
            onChange={setConfidenceThreshold}
          />

          {/* Thinking Delay Slider */}
          <DynamicSlider
            label="Detection Consensus Delay"
            value={thinkingDuration}
            min={1.0}
            max={10.0}
            step={0.5}
            unit="s"
            hint={`${thinkingDuration.toFixed(1)}s Multi-Frame Consensus`}
            description="Duration the AI continuously samples frames before locking the category and throwing."
            color="#d97706"
            onChange={setThinkingDuration}
          />

          {/* ROI Size Slider */}
          <DynamicSlider
            label="Target Zone (ROI) Size"
            value={roiSize}
            min={25}
            max={85}
            step={5}
            unit="%"
            hint={`${roiSize}% Center Crop`}
            description="Width and height proportion of the central camera frame analyzed by YOLO."
            color="#059669"
            onChange={setRoiSize}
          />
        </div>
      </Panel>

      {/* 3. Operational Behavior */}
      <Panel
        title="Operational Automation & Safety Behavior"
        icon={<Settings2 className="size-4 text-purple-600" />}
        className="lg:col-span-2"
      >
        <div className="grid gap-3 sm:grid-cols-2">
          <DynamicToggle
            label="Auto-Start AI Detection on Startup"
            description="Automatically activates YOLO detection when the camera stream initializes."
            checked={autoStart}
            onChange={setAutoStart}
          />
          <DynamicToggle
            label="Log Every Detection to Database"
            description="Persists all classification events, confidence levels, and timestamps in SQLite."
            checked={logDetections}
            onChange={setLogDetections}
          />
          <DynamicToggle
            label="Audio Notification on Sort"
            description="Plays an audible confirmation chime when a category throw routine executes."
            checked={playSound}
            onChange={setPlaySound}
          />
          <DynamicToggle
            label="Return to Home Position After Sort"
            description="Automatically repositions the 6-DOF arm to neutral Home (90°) upon receiving 'Done'."
            checked={returnToHome}
            onChange={setReturnToHome}
          />
        </div>

        {/* Save Changes Button */}
        <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
          <span className="font-mono text-xs text-slate-500">
            Changes take effect immediately across backend & computer vision threads.
          </span>
          <button
            type="button"
            onClick={handleSaveSettings}
            disabled={saving}
            className={cn(
              'flex items-center gap-2 rounded-xl px-5 py-2.5 font-bold text-sm shadow-md transition-all duration-200',
              saveSuccess
                ? 'bg-emerald-600 text-white shadow-emerald-200'
                : 'bg-sky-600 text-white hover:bg-sky-700 hover:scale-105 active:scale-95 shadow-sky-200'
            )}
          >
            {saveSuccess ? (
              <>
                <CheckCircle2 className="size-4 text-white" />
                <span>SETTINGS APPLIED!</span>
              </>
            ) : saving ? (
              <>
                <RefreshCw className="size-4 animate-spin text-white" />
                <span>APPLYING...</span>
              </>
            ) : (
              <>
                <Save className="size-4 text-white" />
                <span>APPLY & SAVE SETTINGS</span>
              </>
            )}
          </button>
        </div>
      </Panel>
    </div>
  )
}

function DynamicSlider({
  label,
  value,
  min,
  max,
  step = 1,
  unit,
  hint,
  description,
  color,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  step?: number
  unit: string
  hint: string
  description: string
  color: string
  onChange: (val: number) => void
}) {
  return (
    <div className="flex flex-col gap-2 rounded-xl bg-slate-50/80 p-3.5 border border-slate-200">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-slate-900">{label}</span>
        <span
          className="font-mono text-xs font-black px-2 py-0.5 rounded border"
          style={{ color, borderColor: `${color}40`, background: `${color}10` }}
        >
          {hint}
        </span>
      </div>
      <p className="text-xs text-slate-500 leading-tight">{description}</p>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-sky-600 mt-1"
      />
      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  )
}

function DynamicToggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  onChange: (val: boolean) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={cn(
        'flex items-start justify-between rounded-xl border p-3.5 text-left transition-all duration-150',
        checked
          ? 'border-sky-400 bg-sky-50/70'
          : 'border-slate-200 bg-white hover:bg-slate-50'
      )}
    >
      <div className="pr-3">
        <span className="text-sm font-bold text-slate-900 block">{label}</span>
        <span className="text-xs text-slate-500 mt-0.5 block leading-tight">{description}</span>
      </div>
      <span
        className={cn(
          'relative h-6 w-11 shrink-0 rounded-full transition-colors duration-200 mt-0.5',
          checked ? 'bg-sky-600' : 'bg-slate-300'
        )}
      >
        <span
          className={cn(
            'absolute top-1 size-4 rounded-full bg-white transition-transform duration-200 shadow-xs',
            checked ? 'translate-x-6' : 'translate-x-1'
          )}
        />
      </span>
    </button>
  )
}
