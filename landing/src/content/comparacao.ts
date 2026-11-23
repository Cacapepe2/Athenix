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
export const CLASSES_HISTORICAS = { novo: 'novo', alterado: 'alterado', ja_existia: 'já existia' }
export function resumoComparacao(p: PlanoDados): string | null {
  const r = p.comparacao_anterior?.resumo
  return r ? `${r.novo} novos · ${r.alterado} alterados · ${r.ja_existia} já existiam` : null
}
