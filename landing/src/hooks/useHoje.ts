import { useEffect, useState } from 'react'
import { hojeISO } from '../content/datas'

/**
 * "Hoje" (AAAA-MM-DD, fuso America/Sao_Paulo) só depois da montagem no navegador; null no HTML pré-renderizado
 * e na hidratação. A pré-renderização acontece no build (outro dia, em UTC); se ela escrevesse a data, o HTML
 * divergiria do primeiro render do cliente (erro 418 do React). Quem usa mostra um estado neutro enquanto for null.
 */
export function useHoje(): string | null {
  const [hoje, setHoje] = useState<string | null>(null)
  useEffect(() => setHoje(hojeISO()), [])
  return hoje
}
