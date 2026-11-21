// "Quem faz o quê": tarefas por área (CSV) e prazos para o calendário (.ics). Lógica pura, testada em
// tarefas.test.ts. As áreas são SUGESTÃO (athenix/data/areas_por_tipo.json); nada sai do navegador.
import { brlCurto, celula, dataBR, pct } from './plano.ts'
import type { BlocoPlano } from './filtros.ts'

export const COLUNAS_TAREFAS = ['obrigação', 'dispositivo', 'prazo', 'valor por infração', 'ação recomendada', 'o que provar', 'norma', 'área (sugestão)'] as const

const valorTexto = (b: BlocoPlano) => (b.valor ? (b.valor.reais != null ? brlCurto(b.valor.reais) : `${pct(b.valor.pct)} da receita`) + (b.preliminar ? ' (preliminar)' : '') : 'a enquadrar')

/** Uma linha por obrigação da área (ou de todas, se `area` for null), na ordem da executiva. */
export function tarefasCsv(blocos: BlocoPlano[], area: string | null): string {
  const linhas = blocos.filter((b) => !area || b.area === area)
  const corpo = linhas.map((b) => [b.frase, b.dispositivo ?? '', b.prazoCurto, valorTexto(b), b.fazer?.texto ?? 'recomendação em revisão', b.proveCom ?? '', b.normaRotulo, b.area].map(celula).join(','))
  return [COLUNAS_TAREFAS.map(celula).join(','), ...corpo].join('\r\n') + '\r\n'
}

// ---------- calendário (.ics) ----------

const escapar = (t: string) => t.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n')
const dia = (iso: string) => iso.replace(/-/g, '')

/** Dobra a linha em 75 caracteres (RFC 5545). */
export function dobrar(linha: string): string {
  const partes: string[] = []
  let resto = linha
  while (resto.length > 75) { partes.push(resto.slice(0, 75)); resto = ` ${resto.slice(75)}` }
  partes.push(resto)
  return partes.join('\r\n')
}

/** Regra de repetição lida do texto da obrigação recorrente; null se a periodicidade não aparece. */
export function recorrenciaDoTexto(texto: string): string | null {
  const t = texto.toLowerCase()
  if (/semestral/.test(t)) return 'FREQ=MONTHLY;INTERVAL=6'
  if (/trimestral/.test(t)) return 'FREQ=MONTHLY;INTERVAL=3'
  if (/mensal/.test(t)) return 'FREQ=MONTHLY'
  if (/anual|a cada per[ií]odo de 12 meses/.test(t)) return 'FREQ=YEARLY'
  return null
}

export interface EntradaCalendario { norma: string; vigencia: string; blocos: BlocoPlano[]; trechos: Record<string, string> }

/** Prazos com data viram eventos de dia inteiro; recorrentes viram evento com RRULE a partir da vigência da norma
 *  (data de partida estimada, dito na descrição). Sem data e sem periodicidade, a obrigação não entra. */
export function calendarioIcs(entradas: EntradaCalendario[], area: string | null, agora = new Date()): string {
  const carimbo = agora.toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z')
  const eventos: string[] = []
  for (const e of entradas) {
    for (const b of e.blocos) {
      if (area && b.area !== area) continue
      const rec = b.situacaoPrazo === 'recorrente' ? recorrenciaDoTexto(e.trechos[b.id] ?? '') : null
      const data = b.dataPrazo
      if (!data && !rec) continue
      const desc = `${b.normaRotulo} · ${b.dispositivo ?? ''}. Área sugerida: ${b.area}. ${data ? `Prazo provisório${b.prazoBase ? ` (${b.prazoBase})` : ''}.` : `Recorrente; data de partida estimada na vigência da norma (${dataBR(e.vigencia)}).`} Análise preliminar, não é parecer jurídico.`
      eventos.push([
        'BEGIN:VEVENT', `UID:${b.norma}-${b.id}@athenix`, `DTSTAMP:${carimbo}`, `DTSTART;VALUE=DATE:${dia(data ?? e.vigencia)}`,
        ...(rec ? [`RRULE:${rec}`] : []), `SUMMARY:${escapar(`${data ? 'Prazo' : 'Recorrente'}: ${b.titulo} (${b.dispositivo ?? ''})`)}`, `DESCRIPTION:${escapar(desc)}`, 'END:VEVENT',
      ].map(dobrar).join('\r\n'))
    }
  }
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Athenix//Prazos//PT', 'CALSCALE:GREGORIAN', ...eventos, 'END:VCALENDAR'].join('\r\n') + '\r\n'
}
