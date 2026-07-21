import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from 'react'

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' | 'danger' }) {
  const styles = {
    primary:
      'bg-accent hover:bg-accent-hover text-white disabled:bg-line disabled:text-slate-500',
    ghost:
      'bg-transparent hover:bg-surface-overlay text-slate-300 border border-line',
    danger: 'bg-rose-600/80 hover:bg-rose-600 text-white',
  }[variant]
  return (
    <button
      className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${styles} ${className}`}
      {...props}
    />
  )
}

export function Card({
  title,
  children,
  className = '',
  actions,
}: {
  title?: ReactNode
  children: ReactNode
  className?: string
  actions?: ReactNode
}) {
  return (
    <div className={`rounded-xl border border-line bg-surface-raised p-5 ${className}`}>
      {(title || actions) && (
        <div className="mb-4 flex items-center justify-between">
          {title && <h3 className="text-sm font-semibold text-slate-100">{title}</h3>}
          {actions}
        </div>
      )}
      {children}
    </div>
  )
}

export function Input({
  className = '',
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-slate-200 outline-none placeholder:text-slate-600 focus:border-accent ${className}`}
      {...props}
    />
  )
}

export function Badge({
  children,
  tone = 'default',
  title,
}: {
  children: ReactNode
  tone?: 'default' | 'success' | 'warning' | 'error' | 'accent'
  title?: string
}) {
  const styles = {
    default: 'bg-surface-overlay text-slate-300',
    success: 'bg-emerald-500/15 text-emerald-400',
    warning: 'bg-amber-500/15 text-amber-400',
    error: 'bg-rose-500/15 text-rose-400',
    accent: 'bg-accent/15 text-accent-hover',
  }[tone]
  return (
    <span
      title={title}
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles}`}
    >
      {children}
    </span>
  )
}

export function Progress({ value }: { value: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-surface-overlay">
      <div
        className="h-full rounded-full bg-accent transition-[width] duration-500"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  )
}

export function SliderRow({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  step?: number
  onChange: (v: number) => void
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <input
          type="number"
          className="w-24 rounded-md border border-line bg-surface px-2 py-0.5 text-right text-xs text-slate-200 outline-none focus:border-accent"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(e) => onChange(Number(e.target.value))}
        />
      </div>
      <input
        type="range"
        className="w-full accent-indigo-500"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  )
}

export function Switch({
  checked,
  onChange,
  label,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  label: string
}) {
  return (
    <label className="flex cursor-pointer items-center justify-between text-sm">
      <span className="text-slate-400">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 rounded-full transition-colors ${checked ? 'bg-accent' : 'bg-surface-overlay'}`}
      >
        <span
          className={`absolute left-0 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`}
        />
      </button>
    </label>
  )
}

export function Spinner() {
  return (
    <div className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-accent" />
  )
}
