interface Props {
  tone?: 'dark' | 'light'
  showWordmark?: boolean
  className?: string
}

export function LogoMark({ className = 'h-7 w-7' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <path d="M2.5 28 13.2 4h5.1L7.6 28z" fill="#B6A38B" />
      <path d="M16.6 11.2 19.4 5 29.5 28h-5.1z" fill="currentColor" />
    </svg>
  )
}

export function Logo({ tone = 'dark', showWordmark = true, className = '' }: Props) {
  const color = tone === 'dark' ? 'text-obsidian' : 'text-ivory'
  return (
    <span className={`inline-flex items-center gap-2.5 ${color} ${className}`}>
      <LogoMark />
      {showWordmark && <span className="font-display text-[1.6rem] leading-none font-medium tracking-tight">Athenix</span>}
    </span>
  )
}
