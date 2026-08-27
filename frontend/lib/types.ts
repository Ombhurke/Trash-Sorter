export type SystemState = 'WAITING' | 'THINKING' | 'OPERATING' | 'EMERGENCY'

export type OperatingMode = 'AUTONOMOUS' | 'MANUAL'

export type WasteCategory = 'PLASTIC' | 'PAPER' | 'METAL' | 'GLASS' | 'CARDBOARD'

export interface CategoryMeta {
  key: WasteCategory
  label: string
  code: string
  hotkey: string
  color: string
  bin: string
}

export interface Detection {
  id: string
  category: WasteCategory
  label: string
  confidence: number
  code: string
  timestamp: string
}

export interface ArmAngles {
  base: number
  shoulder: number
  elbow: number
  wrist: number
  gripper: number
}

export interface HealthCheck {
  key: string
  label: string
  detail: string
  ok: boolean
}

export interface SerialLogEntry {
  timestamp: string
  direction: 'TX' | 'RX' | 'INFO' | 'ERROR' | string
  data: string
}

export interface Telemetry {
  state: SystemState
  mode: OperatingMode
  detectionActive?: boolean
  fps: number
  thinkingProgress: number
  arm: ArmAngles
  lastDetection: Detection
  counts: Record<WasteCategory, number>
  hourlyThroughput?: { hour: string; items: number }[]
  health: HealthCheck[]
  connected: boolean
  hardwareConnected?: boolean
  serialPort?: string
  baudRate?: number
  availablePorts?: string[]
  availablePortsInfo?: { port: string; description: string; hwid?: string }[]
  serialLogs?: SerialLogEntry[]
  uptime?: string
  modelName?: string
  wsActive: boolean
}

export interface ManualCommand {
  action: WasteCategory | 'HOME' | 'RESET' | 'STOP'
  code: string
}

export const CATEGORIES: CategoryMeta[] = [
  { key: 'PLASTIC', label: 'Plastic', code: 'P', hotkey: 'P', color: 'var(--cyan)', bin: 'Right Bin (Blue)' },
  { key: 'PAPER', label: 'Paper', code: 'A', hotkey: 'A', color: 'var(--emerald)', bin: 'Far Right Bin (Green)' },
  { key: 'METAL', label: 'Metal', code: 'M', hotkey: 'M', color: 'var(--amber)', bin: 'Far Left Bin (Yellow)' },
  { key: 'GLASS', label: 'Glass', code: 'G', hotkey: 'G', color: 'var(--purple)', bin: 'Left Bin (Gray)' },
  { key: 'CARDBOARD', label: 'Cardboard', code: 'C', hotkey: 'C', color: 'var(--orange)', bin: 'Back Bin (Brown)' },
]

export const CATEGORY_MAP: Record<WasteCategory, CategoryMeta> = CATEGORIES.reduce(
  (acc, c) => {
    acc[c.key] = c
    return acc
  },
  {} as Record<WasteCategory, CategoryMeta>,
)
