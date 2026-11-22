import type { ReactNode } from 'react'
import { fonteDaCitacao } from '../../content/fontes'

export function LinkFonte({ sha256, trecho, children }: { sha256: string; trecho: string | null | undefined; children: ReactNode }) {
  const href = fonteDaCitacao(sha256, trecho)
  return href ? <a className="underline underline-offset-4" href={href} target="_blank" rel="noopener noreferrer" title="Abrir fonte oficial">{children}</a> : <span>{children}</span>
}
