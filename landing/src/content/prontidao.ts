// Prontidão para fiscalização: "se a ANEEL fiscalizar amanhã, vocês têm prova para X de N obrigações".
// Critério (aparece em "Como calculamos"): uma obrigação conta quando TODAS as provas sugeridas para ela no
// checklist do tema estão marcadas ("temos isto"); obrigação sem prova no checklist não conta. N é o total de
// obrigações do plano. É contagem de quem marcou, não prova de cumprimento. Lógica pura, testada.
import { recomendacoesDoTema } from './recomendacoes.ts'
import type { Modo, PlanoDados, Simulacao } from './plano.ts'
import type { Respostas } from './respostas.ts'

export interface Prontidao {
  porTema: Record<string, { x: number; n: number }>
  geral: { x: number; n: number }
  /** Só mostra o indicador depois de o usuário marcar alguma prova. */
  algumaMarcada: boolean
}

export const CRITERIO_PRONTIDAO = 'Conta a obrigação cujas provas sugeridas no checklist do tema estão todas marcadas como “temos isto”. Obrigação sem prova no checklist não conta. É a contagem do que vocês marcaram, não uma garantia de cumprimento.'

export function prontidao(p: PlanoDados, r: Respostas, s: Simulacao | null = null, modo: Modo = 'preliminar'): Prontidao {
  const por = new Map(p.obrigacoes.map((o) => [o.id, o]))
  const porTema: Prontidao['porTema'] = {}
  let x = 0
  for (const t of p.temas) {
    const marcadas = new Set(r.provas[t.id] ?? [])
    const checklist = recomendacoesDoTema(p, t, s, modo).provas
    let xt = 0
    for (const id of t.obrigacoes) {
      const o = por.get(id)
      const tipo = o?.analise?.tipo?.id ?? o?.analise?.tipo?.regra_id
      const suas = checklist.filter((c) => c.id.startsWith(`${tipo}:`))
      if (suas.length && suas.every((c) => marcadas.has(c.id))) xt++
    }
    porTema[t.id] = { x: xt, n: t.obrigacoes.length }
    x += xt
  }
  return { porTema, geral: { x, n: p.obrigacoes.length }, algumaMarcada: Object.values(r.provas).some((v) => v.length > 0) }
}

export const fraseProntidao = (x: number, n: number) => `Se a ANEEL fiscalizar amanhã, vocês têm prova para ${x} de ${n} obrigações`
