'use client'

import dynamic from 'next/dynamic'

const DashboardShell = dynamic(
  () => import('@/components/dashboard-shell').then((mod) => mod.DashboardShell),
  {
    ssr: false,
    loading: () => (
      <div className="flex min-h-dvh items-center justify-center bg-slate-50 font-mono text-sm text-slate-500">
        <div className="flex flex-col items-center gap-3">
          <div className="size-8 animate-spin rounded-full border-2 border-sky-600 border-t-transparent" />
          <span>Initializing Veg QX Sorter Dashboard...</span>
        </div>
      </div>
    ),
  }
)

export default function Page() {
  return <DashboardShell />
}
