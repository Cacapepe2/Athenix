import { ChevronDown } from 'lucide-react'

/** Chevron do <summary>: gira quando o <details> está aberto (regra em index.css). */
export const Chevron = ({ className = 'ml-auto h-5 w-5' }: { className?: string }) => <ChevronDown aria-hidden="true" className={`chevron shrink-0 text-slate-blue transition-transform ${className}`} />
