// Filtros do plano completo (/demo): norma, situação, gravidade e enquadramento. Ficam na URL
// (?norma=…&situacao=…) para o link ser compartilhável. Lógica pura, testada em filtros.test.ts.
import { NORMAS, top5, type LinhaTop5 } from './executivo.ts'
import type { Modo, NormaId, Simulacao } from './plano.ts'

export type FiltroNorma = 'todas' | NormaId
export type FiltroSituacao = 'todas' | 'vencida' | 'a-vencer' | 'recorrente' | 'sem-prazo'
export type FiltroGravidade = 'todas' | 'grave' | 'seria' | 'media' | 'a-enquadrar'
export type FiltroEnquadramento = 'todas' | 'identificado' | 'sugerido'

export interface Filtros { norma: FiltroNorma; situacao: FiltroSituacao; gravidade: FiltroGravidade; enquadramento: FiltroEnquadramento }
export const FILTROS_INICIAIS: Filtros = { norma: 'todas', situacao: 'todas', gravidade: 'todas', enquadramento: 'todas' }

export const OPCOES: { chave: keyof Filtros; titulo: string; opcoes: { valor: string; rotulo: string }[] }[] = [
  { chave: 'norma', titulo: 'Norma', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, ...NORMAS.map((n) => ({ valor: n.id, rotulo: n.rotulo.replace('/2025', '').replace('/2026', '') }))] },
  { chave: 'situacao', titulo: 'Situação', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, { valor: 'vencida', rotulo: 'Vencida' }, { valor: 'a-vencer', rotulo: 'A vencer' }, { valor: 'recorrente', rotulo: 'Recorrente' }, { valor: 'sem-prazo', rotulo: 'Sem prazo fixo' }] },
  { chave: 'gravidade', titulo: 'Gravidade', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, { valor: 'grave', rotulo: 'Grave' }, { valor: 'seria', rotulo: 'Séria' }, { valor: 'media', rotulo: 'Média' }, { valor: 'a-enquadrar', rotulo: 'A enquadrar' }] },
  { chave: 'enquadramento', titulo: 'Enquadramento', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, { valor: 'identificado', rotulo: 'Identificado no texto' }, { valor: 'sugerido', rotulo: 'Sugerido' }] },
]

const permitido = (chave: keyof Filtros, valor: string | null) => (valor && OPCOES.find((o) => o.chave === chave)!.opcoes.some((x) => x.valor === valor) ? valor : 'todas')

/** Lê os filtros da URL; valor desconhecido vira "todas" (nada quebra com um link antigo). */
export function filtrosDaUrl(search: string): Filtros {
  const q = new URLSearchParams(search)
  const f = { ...FILTROS_INICIAIS }
  for (const o of OPCOES) (f[o.chave] as string) = permitido(o.chave, q.get(o.chave))
  return f
}

/** Aplica os filtros à query atual, preservando os outros parâmetros (?tema=…); "todas" sai da URL. */
export function urlComFiltros(search: string, f: Filtros): string {
  const q = new URLSearchParams(search)
  for (const o of OPCOES) {
    if (f[o.chave] === 'todas') q.delete(o.chave)
    else q.set(o.chave, f[o.chave])
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

export interface BlocoPlano extends LinhaTop5 { norma: NormaId; normaRotulo: string }

const SITUACAO: Record<LinhaTop5['situacaoPrazo'], FiltroSituacao> = { vencida: 'vencida', '90dias': 'a-vencer', depois: 'a-vencer', recorrente: 'recorrente', evento: 'sem-prazo', sem_prazo: 'sem-prazo' }
const GRAVIDADE: Record<string, FiltroGravidade> = { IV: 'grave', III: 'seria', II: 'media' }

export const situacaoDoBloco = (b: LinhaTop5): FiltroSituacao => SITUACAO[b.situacaoPrazo]
export const gravidadeDoBloco = (b: LinhaTop5): FiltroGravidade | 'outra' => (b.valor ? GRAVIDADE[b.valor.grupo] ?? 'outra' : 'a-enquadrar')

/** Todas as obrigações das duas normas, já na ordem da executiva (vencidas, a vencer, maior valor). */
export function blocosDoPlano(s: Simulacao | null, modo: Modo): BlocoPlano[] {
  return NORMAS.flatMap((n) => top5(n.id, s, modo, n.dados.obrigacoes.length).map((l) => ({ ...l, norma: n.id, normaRotulo: n.rotulo })))
}

export function filtrar(blocos: BlocoPlano[], f: Filtros): BlocoPlano[] {
  return blocos.filter((b) =>
    (f.norma === 'todas' || b.norma === f.norma)
    && (f.situacao === 'todas' || situacaoDoBloco(b) === f.situacao)
    && (f.gravidade === 'todas' || gravidadeDoBloco(b) === f.gravidade)
    && (f.enquadramento === 'todas' || b.valor?.origem === f.enquadramento))
}
