import type { AnchorHTMLAttributes, ReactNode } from 'react'
import { ArrowRight } from 'lucide-react'

type Variant = 'primary' | 'secondary' | 'bronze' | 'ghost-dark'

const styles: Record<Variant, string> = {
  primary:
    'bg-slate-blue text-ivory shadow-[0_1px_0_rgb(255_255_255/0.12)_inset,0_10px_24px_-12px_rgb(17_28_47/0.6)] hover:bg-obsidian',
  secondary: 'border border-obsidian/15 bg-white/60 text-obsidian backdrop-blur hover:border-obsidian/35 hover:bg-white',
  bronze: 'bg-bronze text-obsidian hover:bg-[#c5b49d] shadow-[0_10px_30px_-12px_rgb(182_163_139/0.6)]',
  'ghost-dark': 'border border-ivory/20 text-ivory hover:border-ivory/45 hover:bg-ivory/5',
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
      className={`group inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 py-2.5 text-[0.95rem] font-medium transition-[background-color,border-color,transform,box-shadow] duration-300 ease-out-expo active:scale-[0.98] ${styles[variant]} ${className}`}
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
