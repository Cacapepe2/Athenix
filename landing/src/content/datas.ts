// Datas no navegador: "vencida há N dias" é sempre contado de HOJE a partir da data de vencimento, nunca
// do número congelado no JSON (que vale para a data de referência da geração). Lógica pura, testada em datas.test.ts.
import type { Obrigacao } from './plano.ts'

/** AAAA-MM-DD no fuso do navegador (toISOString usaria UTC e trocaria o dia à noite). */
export const hojeISO = (d: Date = new Date()): string => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const dias_ = (iso: string) => {
  const [a, m, d] = iso.split('-').map(Number)
  return Date.UTC(a, m - 1, d) / 86_400_000
}

/** Dias de `hoje` até `iso` (negativo: já passou). */
export const diasAte = (iso: string, hoje: string): number => Math.round(dias_(iso) - dias_(hoje))

/** A obrigação com situação e dias recalculados para `hoje` (só as que têm data de vencimento). */
export function atualizar(o: Obrigacao, hoje: string): Obrigacao {
  if (!o.prazo.data) return o
  const dias = diasAte(o.prazo.data, hoje)
  const situacao = dias < 0 ? 'vencida' : dias <= 90 ? '90dias' : 'depois'
  return { ...o, situacao, prazo: { ...o.prazo, dias } }
}
