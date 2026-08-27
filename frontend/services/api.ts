/**
 * Veg QX — Production Sorter IoT API service module.
 * Connects frontend directly to the FastAPI Python backend at http://localhost:8000.
 */

import type { ManualCommand, Telemetry } from '@/lib/types'

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000/ws'

/** MJPEG live video stream endpoint. */
export const VIDEO_FEED_URL = `${API_BASE}/api/video-feed`

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export interface DetectionItem {
  id: string
  timestamp: string
  category: string
  label: string
  confidence: number
  code: string
  status: string
}

export interface LogItem {
  id: number
  timestamp: string
  level: string
  source: string
  message: string
}

export const api = {
  /** GET current full telemetry snapshot. */
  getTelemetry: () => request<Telemetry>('/api/telemetry'),

  /** GET today's aggregated segregation statistics. */
  getStatistics: () => request<{ counts: Telemetry['counts']; total: number }>('/api/statistics'),

  /** GET system health checklist. */
  getHealth: () => request<Telemetry['health']>('/api/health'),

  /** GET historical detections from SQLite. */
  getDetections: (limit = 50, offset = 0, category?: string) =>
    request<{ total: number; offset: number; limit: number; items: DetectionItem[] }>(
      `/api/detections?limit=${limit}&offset=${offset}${category ? `&category=${category}` : ''}`
    ).catch(() => ({ total: 0, offset: 0, limit: 50, items: [] })),

  /** GET system audit logs from SQLite. */
  getLogs: (limit = 50) => request<LogItem[]>(`/api/logs?limit=${limit}`).catch(() => []),

  /** POST a manual override command to the arm controller. */
  sendManualCommand: (command: ManualCommand) =>
    request<{ ok: boolean; message: string }>('/api/control/manual', {
      method: 'POST',
      body: JSON.stringify(command),
    }).catch((err) => ({ ok: false, message: String(err) })),

  /** POST mode change (AUTONOMOUS <-> MANUAL). */
  setMode: (mode: Telemetry['mode']) =>
    request<{ ok: boolean; message: string }>('/api/control/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }).catch((err) => ({ ok: false, message: String(err) })),

  /** POST system reset to Home. */
  resetSystem: () =>
    request<{ ok: boolean; message: string }>('/api/control/reset', { method: 'POST' }).catch(
      (err) => ({ ok: false, message: String(err) })
    ),

  /** POST toggle camera AI detection on/off. */
  toggleDetection: () =>
    request<{ ok: boolean; detectionActive: boolean; message: string }>('/api/vision/toggle', {
      method: 'POST',
    }).catch(() => ({ ok: true, detectionActive: false, message: 'Detection toggled' })),

  /** POST start camera AI detection. */
  startDetection: () =>
    request<{ ok: boolean; detectionActive: boolean; message: string }>('/api/vision/start', {
      method: 'POST',
    }).catch(() => ({ ok: true, detectionActive: true, message: 'Detection started' })),

  /** POST stop/pause camera AI detection. */
  stopDetection: () =>
    request<{ ok: boolean; detectionActive: boolean; message: string }>('/api/vision/stop', {
      method: 'POST',
    }).catch(() => ({ ok: true, detectionActive: false, message: 'Detection paused' })),

  /** GET system settings & available COM ports. */
  getSettings: () =>
    request<{
      available_ports: string[]
      serial_port: string
      baud_rate: number
      confidence_threshold: number
      thinking_duration: number
      roi_size: number
      camera_device: number
      resolution: string
      api_base: string
      auto_start: boolean
      log_detections: boolean
      return_to_home: boolean
    }>('/api/settings').catch(() => ({
      available_ports: ['COM1', 'COM2', 'COM3', 'COM4', 'COM5'],
      serial_port: 'COM3',
      baud_rate: 19200,
      confidence_threshold: 40,
      thinking_duration: 5.0,
      roi_size: 50,
      camera_device: 0,
      resolution: '1280 × 720',
      api_base: 'http://localhost:8000',
      auto_start: true,
      log_detections: true,
      return_to_home: true,
    })),

  /** POST update system settings. */
  updateSettings: (payload: any) =>
    request<any>('/api/settings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** GET detected system serial COM ports and connection state. */
  getSerialPorts: () =>
    request<{
      ports: { port: string; description: string; hwid: string }[]
      connected_port: string | null
      connected: boolean
      baud_rate: number
    }>('/api/serial/ports').catch(() => ({
      ports: [
        { port: 'COM1', description: 'Communications Port (COM1)', hwid: '' },
        { port: 'COM2', description: 'Communications Port (COM2)', hwid: '' },
        { port: 'COM3', description: 'USB-SERIAL CH340 / Arduino UNO (COM3)', hwid: '' },
        { port: 'COM4', description: 'USB Serial Device (COM4)', hwid: '' },
      ],
      connected_port: null,
      connected: false,
      baud_rate: 19200,
    })),

  /** POST connect to selected COM port. */
  connectSerial: (port: string, baudRate: number = 19200) =>
    request<{ ok: boolean; connected: boolean; port: string; baud_rate: number; message: string }>(
      '/api/serial/connect',
      {
        method: 'POST',
        body: JSON.stringify({ port, baud_rate: baudRate }),
      }
    ).catch((err) => ({
      ok: false,
      connected: false,
      port,
      baud_rate: baudRate,
      message: String(err),
    })),

  /** POST disconnect from serial COM port. */
  disconnectSerial: () =>
    request<{ ok: boolean; connected: boolean; message: string }>('/api/serial/disconnect', {
      method: 'POST',
    }).catch((err) => ({ ok: false, connected: false, message: String(err) })),

  /** GET serial monitor connection status & message history. */
  getSerialStatus: () => request<any>('/api/serial/status').catch(() => null),

  /** POST send arbitrary character/command over Serial to Arduino. */
  sendRawSerial: (command: string) =>
    request<{ ok: boolean; message: string }>('/api/serial/send', {
      method: 'POST',
      body: JSON.stringify({ command }),
    }).catch((err) => ({ ok: false, message: String(err) })),

  /** POST clear serial monitor logs. */
  clearSerialLogs: () =>
    request<{ ok: boolean; message: string }>('/api/serial/clear-logs', {
      method: 'POST',
    }).catch(() => ({ ok: true, message: 'Logs cleared' })),
}

/**
 * Subscribe to the real-time telemetry WebSocket with auto-reconnect.
 */
export function subscribeTelemetry(
  onMessage: (data: Telemetry) => void,
  onStatus?: (connected: boolean) => void,
): () => void {
  let socket: WebSocket | null = null
  let isClosedIntentionally = false
  let reconnectTimer: NodeJS.Timeout | null = null

  function connect() {
    try {
      socket = new WebSocket(WS_URL)

      socket.onopen = () => {
        onStatus?.(true)
        if (reconnectTimer) clearTimeout(reconnectTimer)
      }

      socket.onclose = () => {
        onStatus?.(false)
        if (!isClosedIntentionally) {
          reconnectTimer = setTimeout(connect, 2000)
        }
      }

      socket.onerror = () => {
        onStatus?.(false)
      }

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          onMessage(parsed)
        } catch {
          /* ignore malformed frames */
        }
      }
    } catch {
      onStatus?.(false)
      if (!isClosedIntentionally) {
        reconnectTimer = setTimeout(connect, 3000)
      }
    }
  }

  connect()

  return () => {
    isClosedIntentionally = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (socket) socket.close()
  }
}
