// Datas no navegador: "vencida há N dias" é sempre contado de HOJE a partir da data de vencimento, nunca
// do número congelado no JSON (que vale para a data de referência da geração). Lógica pura, testada em datas.test.ts.
import type { Obrigacao } from './plano.ts'

/** Fuso dos prazos da ANEEL: o dia vira em Brasília, não no servidor (UTC) nem no navegador de quem visita. */
export const FUSO = 'America/Sao_Paulo'
const DIA_NO_FUSO = new Intl.DateTimeFormat('en-CA', { timeZone: FUSO, year: 'numeric', month: '2-digit', day: '2-digit' })

/** AAAA-MM-DD no fuso America/Sao_Paulo (23h30 em São Paulo = 02h30 UTC do dia seguinte ainda é o mesmo dia). */
export function hojeISO(d: Date = new Date()): string {
  const p = Object.fromEntries(DIA_NO_FUSO.formatToParts(d).map((x) => [x.type, x.value]))
  return `${p.year}-${p.month}-${p.day}`
}

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
