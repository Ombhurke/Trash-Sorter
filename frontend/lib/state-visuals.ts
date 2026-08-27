import type { SystemState } from '@/lib/types'

export const STATE_VISUALS: Record<
  SystemState,
  { label: string; color: string; dot: string; text: string; ring: string }
> = {
  WAITING: {
    label: 'WAITING FOR ITEM',
    color: 'var(--cyan)',
    dot: 'bg-cyan shadow-[0_0_10px_var(--cyan)]',
    text: 'text-cyan',
    ring: 'ring-cyan/30 bg-cyan/10',
  },
  THINKING: {
    label: 'THINKING',
    color: 'var(--amber)',
    dot: 'bg-amber shadow-[0_0_10px_var(--amber)] animate-status-blink',
    text: 'text-amber',
    ring: 'ring-amber/30 bg-amber/10',
  },
  OPERATING: {
    label: 'ARM OPERATING',
    color: 'var(--emerald)',
    dot: 'bg-emerald shadow-[0_0_10px_var(--emerald)] animate-status-blink',
    text: 'text-emerald',
    ring: 'ring-emerald/30 bg-emerald/10',
  },
  EMERGENCY: {
    label: 'EMERGENCY STOP',
    color: 'var(--rose)',
    dot: 'bg-rose shadow-[0_0_10px_var(--rose)] animate-status-blink',
    text: 'text-rose',
    ring: 'ring-rose/40 bg-rose/10',
  },
}
