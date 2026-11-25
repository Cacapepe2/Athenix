import type { PlanoDados } from './plano.ts'

export type ClasseHistorica = 'novo' | 'alterado' | 'ja_existia'
export interface TrechoHistorico { trecho: string; pagina: number; ultima_pagina: number }
export interface ComparacaoDocumental {
  escopo: string
  limite: string
  fontes: Record<'v2' | 'v3', { arquivo: string; sha256: string; titulo: string; url: string; origem: string }>
  resumo: Record<ClasseHistorica | 'sem_fonte' | 'divergencias_v3', number>
  registros: Record<string, { item: string; classe: ClasseHistorica; confere_v3: boolean }>
  itens: Record<string, { classe: ClasseHistorica; anterior: TrechoHistorico | null; atual: TrechoHistorico }>
}
/** Frase simples para quem lê a obrigação; as fontes e os hashes ficam no JSON do plano. */
export const fraseComparacao = (c: ClasseHistorica): string => ({
  novo: 'Obrigação nova: entrou no Módulo 4 do PRODIST com a RN 1.137.',
  alterado: 'Obrigação alterada pela RN 1.137 no Módulo 4 do PRODIST.',
  ja_existia: 'Obrigação que já existia no Módulo 4 do PRODIST.',
})[c]
/** Linha do topo da executiva; o número vem do comparador. */
export function textoDeveresCriados(p: PlanoDados): string | null {
  const n = p.comparacao_anterior?.resumo.novo
  return n == null ? null : `${n} ${n === 1 ? 'dever criado' : 'deveres criados'} pela RN 1.137 no PRODIST`
}
/** Contagem completa do comparador (página do plano). */
export function resumoComparacao(p: PlanoDados): string | null {
  const r = p.comparacao_anterior?.resumo
  return r ? `${r.novo} novos · ${r.alterado} alterados · ${r.ja_existia} já existiam` : null
}
