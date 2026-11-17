import { Quote, Sparkles, UserRound, Check, X } from 'lucide-react'

export type TagKind = 'source' | 'ai' | 'review' | 'accepted' | 'rejected' | 'fictional' | 'pending'

const config: Record<TagKind, { label: string; cls: string; Icon?: typeof Quote }> = {
  source: { label: 'Texto da norma', cls: 'bg-stone text-bronze-deep', Icon: Quote },
  ai: { label: 'Interpretação da IA', cls: 'bg-slate-blue/10 text-slate-blue', Icon: Sparkles },
  review: { label: 'Aguarda revisão humana', cls: 'bg-[#f6ecd9] text-pending', Icon: UserRound },
  accepted: { label: 'Aceita na revisão', cls: 'bg-slate-blue text-ivory', Icon: Check },
  rejected: { label: 'Rejeitada na revisão', cls: 'bg-obsidian/8 text-ink-soft', Icon: X },
  pending: { label: 'Data pendente', cls: 'bg-[#f6ecd9] text-pending' },
  fictional: { label: 'Dados fictícios', cls: 'border border-dashed border-bronze-deep/50 text-bronze-deep' },
}

export function Tag({ kind, label, className = '' }: { kind: TagKind; label?: string; className?: string }) {
  const { label: fallback, cls, Icon } = config[kind]
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[0.68rem] leading-4 font-medium whitespace-nowrap ${cls} ${className}`}
    >
      {Icon && <Icon aria-hidden="true" className="h-3 w-3" strokeWidth={2.2} />}
      {label ?? fallback}
    </span>
  )
}
