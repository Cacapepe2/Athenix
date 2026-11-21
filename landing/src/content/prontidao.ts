// Prontidão para fiscalização, medida pelo CHECKLIST de provas (não por obrigação): "provas em mãos: X de Y".
// Y é o número de itens do checklist sugerido (até 3 por tema) e X, os que a empresa marcou como "temos isto".
// O checklist é um conjunto sugerido, não a lista de tudo o que a norma pode exigir: o número mostra o
// quanto do checklist está em mãos, nunca "quantas obrigações estão cobertas". Lógica pura, testada.
import { recomendacoesDoTema } from './recomendacoes.ts'
import type { Modo, PlanoDados, Simulacao } from './plano.ts'
import type { Respostas } from './respostas.ts'

export interface Prontidao {
  /** Por tema: x itens do checklist marcados, de y itens. */
  porTema: Record<string, { x: number; y: number }>
  geral: { x: number; y: number }
  /** Só mostra o indicador depois de o usuário marcar alguma prova. */
  algumaMarcada: boolean
}

export const CRITERIO_PRONTIDAO = 'Conta os itens do checklist sugerido (até 3 provas por tema, tiradas do manual do tipo de obrigação) que vocês marcaram como “temos isto”. Y é o tamanho do checklist, não o número de obrigações: o indicador mostra quanto do checklist está em mãos, não quantas obrigações estão cobertas nem se cumprem a norma.'

export function prontidao(p: PlanoDados, r: Respostas, s: Simulacao | null = null, modo: Modo = 'preliminar'): Prontidao {
  const porTema: Prontidao['porTema'] = {}
  let x = 0
  let y = 0
  for (const t of p.temas) {
    const checklist = recomendacoesDoTema(p, t, s, modo).provas
    const marcadas = new Set(r.provas[t.id] ?? [])
    const xt = checklist.filter((c) => marcadas.has(c.id)).length
    porTema[t.id] = { x: xt, y: checklist.length }
    x += xt
    y += checklist.length
  }
  return { porTema, geral: { x, y }, algumaMarcada: Object.values(r.provas).some((v) => v.length > 0) }
}

/** "Provas em mãos: X de Y (checklist sugerido)". */
export const fraseProntidao = (x: number, y: number) => `Provas em mãos: ${x} de ${y} (checklist sugerido)`
