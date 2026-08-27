import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Panel({
  title,
  icon,
  action,
  className,
  bodyClassName,
  children,
}: {
  title?: string
  icon?: ReactNode
  action?: ReactNode
  className?: string
  bodyClassName?: string
  children: ReactNode
}) {
  return (
    <section className={cn('glass flex flex-col rounded-2xl transition-transform duration-200 hover:-translate-y-0.5', className)}>
      {title && (
        <header className="flex items-center gap-2.5 border-b border-border px-4 py-3">
          {icon && <span className="text-primary">{icon}</span>}
          <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
          {action && <div className="ml-auto flex items-center gap-1.5">{action}</div>}
        </header>
      )}
      <div className={cn('flex-1 p-4', bodyClassName)}>{children}</div>
    </section>
  )
}
