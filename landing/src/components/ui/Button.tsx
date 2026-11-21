import type { AnchorHTMLAttributes, ReactNode } from 'react'
import { ArrowRight } from 'lucide-react'

type Variant = 'primary' | 'secondary' | 'bronze' | 'ghost-dark'

const styles: Record<Variant, string> = {
  primary:
    'border-2 border-obsidian bg-obsidian text-ivory hover:bg-ink-soft hover:border-ink-soft',
  secondary: 'border-2 border-obsidian bg-white text-obsidian hover:bg-stone',
  bronze: 'border-2 border-acento bg-acento text-white hover:border-acento-hover hover:bg-acento-hover',
  'ghost-dark': 'border-2 border-ivory text-ivory hover:bg-ivory/15',
}

interface Props extends AnchorHTMLAttributes<HTMLAnchorElement> {
  variant?: Variant
  arrow?: boolean
  children: ReactNode
}

export function ButtonLink({ variant = 'primary', arrow = true, className = '', children, ...rest }: Props) {
  return (
    <a
      {...rest}
      className={`group inline-flex min-h-11 items-center justify-center gap-2 px-5 py-2.5 text-[0.95rem] font-medium transition-[background-color,border-color,transform,box-shadow] duration-300 ease-out-expo ${styles[variant]} ${className}`}
    >
      {children}
      {arrow && (
        <ArrowRight
          aria-hidden="true"
          className="h-4 w-4 transition-transform duration-300 ease-out-expo group-hover:translate-x-1"
        />
      )}
    </a>
  )
}
