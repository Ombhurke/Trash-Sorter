'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useRef } from 'react'
import * as THREE from 'three'
import type { Telemetry } from '@/lib/types'

const COLORS = ['#1769e8', '#19b96b', '#f3a400', '#7c3aed', '#f59e0b']

function Bars({ values }: { values: number[] }) {
  const group = useRef<THREE.Group>(null)
  useFrame((_, delta) => { if (group.current) group.current.rotation.y += delta * 0.12 })
  const max = Math.max(...values, 1)
  return <group ref={group}>{values.map((value, i) => { const h = 0.35 + (value / max) * 1.9; return <mesh key={i} position={[(i - 2) * 0.65, h / 2 - 1.05, 0]}><boxGeometry args={[0.42, h, 0.42]} /><meshStandardMaterial color={COLORS[i]} roughness={0.3} metalness={0.25} emissive={COLORS[i]} emissiveIntensity={0.08} /></mesh> })}</group>
}

export function StatsBars3D({ telemetry }: { telemetry: Telemetry }) {
  const values = Object.values(telemetry.counts)
  return <div className="h-48 w-full overflow-hidden rounded-xl bg-[#e8eef5]" aria-label="Animated 3D waste category bars">
    <Canvas camera={{ position: [0, 1.7, 5], fov: 42 }}>
      <color attach="background" args={['#e8eef5']} /><ambientLight intensity={1.4} /><directionalLight position={[2, 4, 5]} intensity={3} /><Bars values={values} /><gridHelper args={[6, 10, '#c4d0dd', '#d7e0e9']} position={[0, -1.05, 0]} /><OrbitControls enablePan={false} enableZoom={false} />
    </Canvas>
  </div>
}
