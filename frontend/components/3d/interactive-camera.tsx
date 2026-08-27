'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { ContactShadows, Float, OrbitControls } from '@react-three/drei'
import { useRef } from 'react'
import * as THREE from 'three'
import type { WasteCategory } from '@/lib/types'

const COLORS: Record<WasteCategory, string> = {
  PLASTIC: '#1769e8', PAPER: '#19b96b', METAL: '#f3a400', GLASS: '#7c3aed', CARDBOARD: '#f59e0b',
}

function Conveyor({ category }: { category: WasteCategory }) {
  const belt = useRef<THREE.Mesh>(null)
  useFrame((_, delta) => { if (belt.current) belt.current.rotation.z += delta * 0.7 })
  return <>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.25, 0]}>
      <boxGeometry args={[7, 3.2, 0.18]} /><meshStandardMaterial color="#8b7668" roughness={0.7} />
    </mesh>
    <mesh ref={belt} rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.13, 0]}>
      <planeGeometry args={[6.5, 2.8]} /><meshStandardMaterial color="#b89d8b" roughness={0.8} />
    </mesh>
    <mesh position={[0, -0.95, -1.45]}><boxGeometry args={[7, 0.45, 0.12]} /><meshStandardMaterial color="#263a58" /></mesh>
    <mesh position={[0, -0.95, 1.45]}><boxGeometry args={[7, 0.45, 0.12]} /><meshStandardMaterial color="#263a58" /></mesh>
    <Float speed={2} rotationIntensity={0.2} floatIntensity={0.25}>
      <mesh position={[0, -0.5, 0]}>
        <cylinderGeometry args={[0.38, 0.3, 1.25, 32]} /><meshStandardMaterial color={COLORS[category]} roughness={0.25} metalness={0.1} />
      </mesh>
      <mesh position={[0, 0.18, 0]}><cylinderGeometry args={[0.25, 0.25, 0.12, 32]} /><meshStandardMaterial color="#18345c" metalness={0.4} /></mesh>
    </Float>
    <mesh position={[0, 0.1, 0]}><sphereGeometry args={[0.12, 16, 16]} /><meshBasicMaterial color={COLORS[category]} /></mesh>
  </>
}

export function InteractiveCamera({ category }: { category: WasteCategory }) {
  return <div className="absolute inset-0" aria-label="Animated 3D sorting camera scene">
    <Canvas camera={{ position: [0, 1.4, 5.4], fov: 38 }} dpr={[1, 1.5]}>
      <color attach="background" args={['#d8dde3']} />
      <ambientLight intensity={1.8} /><directionalLight position={[3, 5, 4]} intensity={3} color="#ffffff" /><pointLight position={[-3, 2, 2]} intensity={3} color={COLORS[category]} />
      <Conveyor category={category} /><ContactShadows position={[0, -1.16, 0]} opacity={0.3} scale={8} blur={2.5} far={4} />
      <OrbitControls enableZoom={false} enablePan={false} enableRotate={false} />
    </Canvas>
  </div>
}

export function RobotArmScene({ angles }: { angles: { base: number; shoulder: number; elbow: number; wrist: number; gripper: number } }) {
  return <div className="h-52 w-full overflow-hidden rounded-xl bg-[#e8eef5]" aria-label="Animated 3D robot arm visualization">
    <Canvas camera={{ position: [3.8, 2.5, 5], fov: 40 }}>
      <color attach="background" args={['#e8eef5']} /><ambientLight intensity={1.4} /><directionalLight position={[3, 5, 4]} intensity={3} />
      <group rotation={[0, THREE.MathUtils.degToRad(angles.base - 90), 0]}>
        <mesh position={[0, -1, 0]}><cylinderGeometry args={[0.7, 0.8, 0.28, 32]} /><meshStandardMaterial color="#1769e8" metalness={0.6} roughness={0.25} /></mesh>
        <mesh position={[0, 0, 0]}><cylinderGeometry args={[0.28, 0.32, 2, 24]} /><meshStandardMaterial color="#263a58" metalness={0.6} /></mesh>
        <group rotation={[0, 0, THREE.MathUtils.degToRad(angles.shoulder - 90)]}>
          <mesh position={[0, 1, 0]}><boxGeometry args={[0.38, 2.1, 0.38]} /><meshStandardMaterial color="#1769e8" metalness={0.55} /></mesh>
          <group position={[0, 2, 0]} rotation={[0, 0, THREE.MathUtils.degToRad(angles.elbow - 90)]}>
            <mesh position={[0, 0.75, 0]}><boxGeometry args={[0.32, 1.6, 0.32]} /><meshStandardMaterial color="#19b96b" metalness={0.45} /></mesh>
            <group position={[0, 1.55, 0]} rotation={[0, 0, THREE.MathUtils.degToRad(angles.wrist - 90)]}><mesh position={[0, 0.25, 0]}><boxGeometry args={[0.25, 0.65, 0.25]} /><meshStandardMaterial color="#f3a400" metalness={0.5} /></mesh><mesh position={[0, 0.62, 0]}><sphereGeometry args={[0.2, 20, 20]} /><meshStandardMaterial color="#e51b2a" emissive="#e51b2a" emissiveIntensity={2} /></mesh></group>
          </group>
        </group>
      </group>
      <gridHelper args={[8, 12, '#c4d0dd', '#d7e0e9']} position={[0, -1.15, 0]} /><OrbitControls enableZoom={false} enablePan={false} />
    </Canvas>
  </div>
}
