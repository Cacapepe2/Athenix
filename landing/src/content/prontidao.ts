// Prontidão para fiscalização: "se a ANEEL fiscalizar amanhã, vocês têm prova para X de N obrigações".
// Critério (aparece em "Como calculamos"): uma obrigação conta quando TODAS as provas sugeridas para ela no
// checklist do tema estão marcadas ("temos isto"); obrigação sem prova no checklist não conta. N é o total de
// obrigações do plano. É contagem de quem marcou, não prova de cumprimento. Lógica pura, testada.
import { recomendacoesDoTema } from './recomendacoes.ts'
import type { Modo, PlanoDados, Simulacao } from './plano.ts'
import type { Respostas } from './respostas.ts'

export interface Prontidao {
  /** x: prova completa; y: parcial (alguma prova marcada, mas não todas); n: total de obrigações. */
  porTema: Record<string, { x: number; y: number; n: number }>
  geral: { x: number; y: number; n: number }
  /** Só mostra o indicador depois de o usuário marcar alguma prova. */
  algumaMarcada: boolean
}

export const CRITERIO_PRONTIDAO = 'Conta a obrigação cujas provas sugeridas no checklist do tema estão todas marcadas como “temos isto” (prova completa); com algumas marcadas e outras não, é parcial. Obrigação sem prova no checklist não conta. É a contagem do que vocês marcaram, não uma garantia de cumprimento.'

export function prontidao(p: PlanoDados, r: Respostas, s: Simulacao | null = null, modo: Modo = 'preliminar'): Prontidao {
  const por = new Map(p.obrigacoes.map((o) => [o.id, o]))
  const porTema: Prontidao['porTema'] = {}
  let x = 0
  let y = 0
  for (const t of p.temas) {
    const marcadas = new Set(r.provas[t.id] ?? [])
    const checklist = recomendacoesDoTema(p, t, s, modo).provas
    let xt = 0
    let yt = 0
    for (const id of t.obrigacoes) {
      const o = por.get(id)
      const tipo = o?.analise?.tipo?.id ?? o?.analise?.tipo?.regra_id
      const suas = checklist.filter((c) => c.id.startsWith(`${tipo}:`))
      if (suas.length && suas.every((c) => marcadas.has(c.id))) xt++
      else if (suas.some((c) => marcadas.has(c.id))) yt++
    }
    porTema[t.id] = { x: xt, y: yt, n: t.obrigacoes.length }
    x += xt
    y += yt
  }
  return { porTema, geral: { x, y, n: p.obrigacoes.length }, algumaMarcada: Object.values(r.provas).some((v) => v.length > 0) }
}

/** "Se a ANEEL fiscalizar amanhã, vocês têm prova completa para X de N obrigações · parcial para Y" (o parcial só aparece se houver). */
export const fraseProntidao = (x: number, n: number, y = 0) => `Se a ANEEL fiscalizar amanhã, vocês têm prova completa para ${x} de ${n} obrigações${y > 0 ? ` · parcial para ${y}` : ''}`
