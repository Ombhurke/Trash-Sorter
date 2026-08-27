'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { api, subscribeTelemetry } from '@/services/api'
import {
  type ManualCommand,
  type OperatingMode,
  type Telemetry,
} from '@/lib/types'

const HOME_ANGLES = { base: 90, shoulder: 30, elbow: 140, wrist: 110, gripper: 15 }

const INITIAL: Telemetry = {
  state: 'WAITING',
  mode: 'AUTONOMOUS',
  detectionActive: false,
  fps: 29.8,
  thinkingProgress: 0,
  arm: { ...HOME_ANGLES },
  lastDetection: {
    id: 'seed',
    category: 'PLASTIC',
    label: 'Plastic Bottle',
    confidence: 98.6,
    code: 'P',
    timestamp: '2026-01-01T10:32:45.000Z',
  },
  counts: { PLASTIC: 38, PAPER: 27, METAL: 19, GLASS: 14, CARDBOARD: 16 },
  health: [
    { key: 'arduino', label: 'Arduino Uno Connected', detail: '19200 Baud · COM3', ok: true },
    { key: 'camera', label: 'USB Camera Feed Active', detail: '1280×720 · 30 FPS', ok: true },
    { key: 'ai', label: 'AI Classification Engine Running', detail: 'CLIP / TFLite · 6.4 ms', ok: true },
    { key: 'servo', label: 'Servo Motors Calibrated & Ready', detail: '6-DOF · PCA9685', ok: true },
    { key: 'db', label: 'SQLite Database Connected', detail: 'waste_sorter.db', ok: true },
  ],
  connected: false,
  wsActive: false,
}

export function useTelemetry() {
  const [data, setData] = useState<Telemetry>(INITIAL)
  const [connected, setConnected] = useState<boolean>(false)
  const isWsConnectedRef = useRef(false)

  // Real-time WebSocket connection to FastAPI backend
  useEffect(() => {
    const unsub = subscribeTelemetry(
      (telemetryUpdate) => {
        isWsConnectedRef.current = true
        setConnected(true)
        setData((prev) => ({
          ...prev,
          ...telemetryUpdate,
          connected: true,
          wsActive: true,
        }))
      },
      (wsStatus) => {
        isWsConnectedRef.current = wsStatus
        setConnected(wsStatus)
        setData((prev) => ({
          ...prev,
          connected: wsStatus,
          wsActive: wsStatus,
        }))
      }
    )

    return () => unsub()
  }, [])

  // Poll initial REST telemetry fallback if WebSocket is connecting
  useEffect(() => {
    let active = true
    async function fetchFallback() {
      if (isWsConnectedRef.current) return
      try {
        const telemetry = await api.getTelemetry()
        if (active) {
          setData((prev) => ({ ...prev, ...telemetry, connected: true }))
          setConnected(true)
        }
      } catch {
        if (active) {
          setConnected(false)
        }
      }
    }
    fetchFallback()
    const interval = setInterval(fetchFallback, 3000)
    return () => {
      active = false
      clearInterval(interval)
    }
  }, [])

  const setMode = useCallback(async (mode: OperatingMode) => {
    setData((prev) => ({ ...prev, mode }))
    try {
      await api.setMode(mode)
    } catch (err) {
      console.error('Failed to update mode on backend:', err)
    }
  }, [])

  const toggleDetection = useCallback(async () => {
    setData((prev) => ({ ...prev, detectionActive: !prev.detectionActive }))
    try {
      const res = await api.toggleDetection()
      if (res && typeof res.detectionActive === 'boolean') {
        setData((prev) => ({ ...prev, detectionActive: res.detectionActive }))
      }
    } catch (err) {
      console.error('Failed to toggle detection:', err)
    }
  }, [])

  const sendCommand = useCallback(async (command: ManualCommand) => {
    if (command.action === 'HOME' || command.action === 'RESET') {
      setData((prev) => ({ ...prev, state: 'WAITING', arm: { ...HOME_ANGLES } }))
      try {
        await api.resetSystem()
      } catch (err) {
        console.error('Failed to reset system:', err)
      }
      return
    }

    // Manual Category command (PLASTIC, PAPER, CARDBOARD, GLASS, METAL)
    setData((prev) => ({ ...prev, state: 'OPERATING' }))
    try {
      await api.sendManualCommand(command)
    } catch (err) {
      console.error('Failed to send manual command:', err)
    }
  }, [])

  const connectSerial = useCallback(async (port: string, baudRate: number = 19200) => {
    try {
      const res = await api.connectSerial(port, baudRate)
      if (res && res.connected) {
        setData((prev) => ({
          ...prev,
          hardwareConnected: true,
          serialPort: res.port || port,
          baudRate: res.baud_rate || baudRate,
        }))
      }
      return res
    } catch (err) {
      console.error('Failed to connect serial port:', err)
      return { ok: false, connected: false, message: String(err) }
    }
  }, [])

  const disconnectSerial = useCallback(async () => {
    try {
      const res = await api.disconnectSerial()
      setData((prev) => ({
        ...prev,
        hardwareConnected: false,
      }))
      return res
    } catch (err) {
      console.error('Failed to disconnect serial port:', err)
      return { ok: false, message: String(err) }
    }
  }, [])

  const sendRawSerial = useCallback(async (command: string) => {
    try {
      return await api.sendRawSerial(command)
    } catch (err) {
      console.error('Failed to send raw serial command:', err)
      return { ok: false, message: String(err) }
    }
  }, [])

  const clearSerialLogs = useCallback(async () => {
    try {
      await api.clearSerialLogs()
      setData((prev) => ({ ...prev, serialLogs: [] }))
    } catch (err) {
      console.error('Failed to clear serial logs:', err)
    }
  }, [])

  return {
    data,
    setMode,
    toggleDetection,
    sendCommand,
    connectSerial,
    disconnectSerial,
    sendRawSerial,
    clearSerialLogs,
  }
}

