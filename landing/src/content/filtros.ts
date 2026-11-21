// Filtros do plano completo (/demo): norma, situação, gravidade e enquadramento. Ficam na URL
// (?norma=…&situacao=…) para o link ser compartilhável. Lógica pura, testada em filtros.test.ts.
import { NORMAS, top5, type LinhaTop5 } from './executivo.ts'
import { planos, type Modo, type NormaId, type Simulacao } from './plano.ts'

export type FiltroNorma = 'todas' | NormaId
export type FiltroSituacao = 'todas' | 'vencida' | 'a-vencer' | 'recorrente' | 'sem-prazo'
export type FiltroGravidade = 'todas' | 'grave' | 'seria' | 'media' | 'leve' | 'gravissima' | 'a-enquadrar'
export type FiltroEnquadramento = 'todas' | 'identificado' | 'sugerido'

export interface Filtros { norma: FiltroNorma; situacao: FiltroSituacao; gravidade: FiltroGravidade; enquadramento: FiltroEnquadramento; area: string }
export const FILTROS_INICIAIS: Filtros = { norma: 'todas', situacao: 'todas', gravidade: 'todas', enquadramento: 'todas', area: 'todas' }

/** Parâmetro de URL de cada filtro. O de norma NÃO é `norma`: esse escolhe o plano da página inteira. */
export const PARAM: Record<keyof Filtros, string> = { norma: 'so_norma', situacao: 'situacao', gravidade: 'gravidade', enquadramento: 'enquadramento', area: 'area' }

export const OPCOES: { chave: keyof Filtros; titulo: string; opcoes: { valor: string; rotulo: string }[] }[] = [
  { chave: 'norma', titulo: 'Norma', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, ...NORMAS.map((n) => ({ valor: n.id, rotulo: n.rotulo.replace('/2025', '').replace('/2026', '') }))] },
  { chave: 'situacao', titulo: 'Situação', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, { valor: 'vencida', rotulo: 'Vencida' }, { valor: 'a-vencer', rotulo: 'A vencer' }, { valor: 'recorrente', rotulo: 'Recorrente' }, { valor: 'sem-prazo', rotulo: 'Sem prazo fixo' }] },
  { chave: 'gravidade', titulo: 'Gravidade', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, { valor: 'grave', rotulo: 'Grave' }, { valor: 'seria', rotulo: 'Séria' }, { valor: 'media', rotulo: 'Média' }, { valor: 'leve', rotulo: 'Leve' }, { valor: 'gravissima', rotulo: 'Gravíssima' }, { valor: 'a-enquadrar', rotulo: 'A enquadrar' }] },
  { chave: 'enquadramento', titulo: 'Enquadramento', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, { valor: 'identificado', rotulo: 'Identificado no texto' }, { valor: 'sugerido', rotulo: 'Sugerido' }] },
  { chave: 'area', titulo: 'Área (sugestão)', opcoes: [{ valor: 'todas', rotulo: 'Todas' }, ...planos.rn1137.analise.areas.lista.map((x) => ({ valor: x, rotulo: x }))] },
]

const permitido = (chave: keyof Filtros, valor: string | null) => (valor && OPCOES.find((o) => o.chave === chave)!.opcoes.some((x) => x.valor === valor) ? valor : 'todas')

/** Lê os filtros da URL; valor desconhecido vira "todas" (nada quebra com um link antigo). */
export function filtrosDaUrl(search: string): Filtros {
  const q = new URLSearchParams(search)
  const f = { ...FILTROS_INICIAIS }
  for (const o of OPCOES) (f[o.chave] as string) = permitido(o.chave, q.get(PARAM[o.chave]))
  return f
}

/** Aplica os filtros à query atual, preservando os outros parâmetros (?tema=…); "todas" sai da URL. */
export function urlComFiltros(search: string, f: Filtros): string {
  const q = new URLSearchParams(search)
  for (const o of OPCOES) {
    if (f[o.chave] === 'todas') q.delete(PARAM[o.chave])
    else q.set(PARAM[o.chave], f[o.chave])
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

export interface BlocoPlano extends LinhaTop5 { norma: NormaId; normaRotulo: string }

const SITUACAO: Record<LinhaTop5['situacaoPrazo'], FiltroSituacao> = { vencida: 'vencida', '90dias': 'a-vencer', depois: 'a-vencer', recorrente: 'recorrente', evento: 'sem-prazo', sem_prazo: 'sem-prazo' }
const GRAVIDADE: Record<string, FiltroGravidade> = { V: 'gravissima', IV: 'grave', III: 'seria', II: 'media', I: 'leve' }

export const situacaoDoBloco = (b: LinhaTop5): FiltroSituacao => SITUACAO[b.situacaoPrazo]
export const gravidadeDoBloco = (b: LinhaTop5): FiltroGravidade | 'outra' => (b.valor ? GRAVIDADE[b.valor.grupo] ?? 'outra' : 'a-enquadrar')

/** Todas as obrigações das duas normas, já na ordem da executiva (vencidas, a vencer, maior valor). */
export function blocosDoPlano(s: Simulacao | null, modo: Modo, hoje?: string): BlocoPlano[] {
  return NORMAS.flatMap((n) => top5(n.id, s, modo, n.dados.obrigacoes.length, hoje).map((l) => ({ ...l, norma: n.id, normaRotulo: n.rotulo })))
}

export function filtrar(blocos: BlocoPlano[], f: Filtros): BlocoPlano[] {
  return blocos.filter((b) =>
    (f.norma === 'todas' || b.norma === f.norma)
    && (f.situacao === 'todas' || situacaoDoBloco(b) === f.situacao)
    && (f.gravidade === 'todas' || gravidadeDoBloco(b) === f.gravidade)
    && (f.enquadramento === 'todas' || b.valor?.origem === f.enquadramento)
    && (f.area === 'todas' || b.area === f.area))
}
