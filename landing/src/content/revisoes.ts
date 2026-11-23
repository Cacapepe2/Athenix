import type { NormaId, Obrigacao, PlanoDados } from './plano.ts'
import type { Armazem } from './respostas.ts'

export const LIMITE_CORRECAO = 200
export type CampoRevisao = 'sujeito' | 'enquadramento' | 'area'
export interface Revisao { estado: 'confirmado' | 'corrigido'; original: string; valor: string }
export type Revisoes = Record<string, Partial<Record<CampoRevisao, Revisao>>>
export const ROTULOS_REVISAO = { sujeito: 'Sujeito implícito', enquadramento: 'Enquadramento', area: 'Área sugerida' }

export function camposDaObrigacao(o: Obrigacao): Partial<Record<CampoRevisao, string>> {
  return {
    ...(o.sujeito_implicito ? { sujeito: 'Distribuidora (sujeito implícito, a revisar)' } : {}),
    enquadramento: o.enquadramento.length ? o.enquadramento.map((e) => `${e.dispositivo} · Grupo ${e.grupo}`).join('; ')
      : o.ia ? `Sugestão da IA: ${o.ia.dispositivo} · Grupo ${o.ia.grupo}` : 'Enquadramento a confirmar',
    area: o.area,
  }
}

const chave = (norma: NormaId, sha: string) => `athenix:revisoes:${norma}:${sha}`
const objeto = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v)

/** Ignora registros inválidos e revisões de valores que já mudaram no plano. */
export function revisoesValidas(dados: unknown, plano: PlanoDados): Revisoes {
  const r: Revisoes = {}
  if (!objeto(dados)) return r
  for (const o of plano.obrigacoes) {
    const salvas = dados[o.id]
    if (!objeto(salvas)) continue
    for (const [campo, original] of Object.entries(camposDaObrigacao(o))) {
      const v = salvas[campo]
      if (!objeto(v) || v.original !== original || typeof v.valor !== 'string' || !v.valor.trim() || v.valor.length > LIMITE_CORRECAO) continue
      if (v.estado !== 'confirmado' && v.estado !== 'corrigido') continue
      if (v.estado === 'confirmado' && v.valor !== original) continue
      const c = campo as CampoRevisao
      r[o.id] = { ...r[o.id], [c]: { estado: v.estado, original, valor: v.valor } }
    }
  }
  return r
}

export function carregarRevisoes(armazem: Armazem | null, norma: NormaId, plano: PlanoDados): Revisoes {
  try {
    return revisoesValidas(JSON.parse(armazem?.getItem(chave(norma, plano.norma.sha256)) ?? '{}'), plano)
  } catch { return {} }
}

export function salvarRevisoes(armazem: Armazem | null, norma: NormaId, plano: PlanoDados, r: Revisoes): boolean {
  try {
    if (!armazem) return false
    armazem.setItem(chave(norma, plano.norma.sha256), JSON.stringify(revisoesValidas(r, plano)))
    return true
  } catch { return false }
}

/** Sem texto, confirma o valor exibido; correção vazia não substitui uma revisão existente. */
export function revisarCampo(r: Revisoes, o: Obrigacao, campo: CampoRevisao, correcao?: string): Revisoes {
  const original = camposDaObrigacao(o)[campo]
  const valor = correcao === undefined ? original : correcao.trim().slice(0, LIMITE_CORRECAO)
  if (!original || !valor) return r
  return { ...r, [o.id]: { ...r[o.id], [campo]: { estado: correcao === undefined ? 'confirmado' : 'corrigido', original, valor } } }
}

export function limparRevisao(r: Revisoes, id: string, campo: CampoRevisao): Revisoes {
  const item = { ...r[id] }
  delete item[campo]
  const copia = { ...r }
  if (Object.keys(item).length) copia[id] = item
  else delete copia[id]
  return copia
}

export function linhasDeRevisao(r: Revisoes, plano: PlanoDados) {
  return Object.entries(revisoesValidas(r, plano)).flatMap(([id, campos]) => {
    const o = plano.obrigacoes.find((x) => x.id === id)!
    return Object.entries(campos).map(([campo, v]) => ({ id, campo: ROTULOS_REVISAO[campo as CampoRevisao], ...v, dispositivo: o.dispositivo, trecho: o.trecho }))
  })
}

export function exportarRevisoes(r: Revisoes, norma: NormaId, plano: PlanoDados): string {
  return JSON.stringify({ rotulo: 'Revisões pessoais — somente neste navegador; não alteram a análise automática', norma, sha256: plano.norma.sha256, revisoes: linhasDeRevisao(r, plano) }, null, 2)
}
