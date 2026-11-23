import fontes from './fontes-publicas.json' with { type: 'json' }
// Dados REAIS da RN ANEEL 1.137/2025, gerados por scripts/exportar_demo_site.py a partir do pipeline do
// Athenix (extração por regras, sem IA). Os valores de impacto são ESTIMATIVA ILUSTRATIVA, com o perfil de
// uma distribuidora ilustrativa (não é empresa real). Nenhum número é digitado aqui: tudo vem do JSON.
// Cada `anchor` é cópia literal do dispositivo citado (verificado em text.test.ts).
import dados from './demo-rn1137.json' with { type: 'json' }

export interface Article {
  id: string
  label: string
  text: string
}

export interface Change {
  id: string
  title: string
  detail: string
  effect: string
  wording: string[]
  articleId: string
}

export interface Impact {
  min: number
  probable: number | null
  probableReason: string
  max: number
  maxPct: number
  groupCapPct: number
  legalCapPct: number | null
  /** Teto legal aplicado sobre a base (ROL) porque o faturamento bruto não foi informado. */
  legalCapUnderestimated: boolean | null
  groups: string[]
  framings: { dispositivo: string; grupo: string; trecho: string; sha256: string }[]
  premises: string[]
  sources: string[]
}

export interface Obligation {
  id: string
  short: string
  title: string
  subject: string
  articleId: string
  anchor: string
  deadline: string
  deadlineDetail: string
  deadlineDate: string | null
  /** Quando a norma não fixa a data, ela fica pendente — nunca é inventada. */
  pending?: string
  /** Posição na fila priorizada; null quando aguarda verificação do enquadramento. */
  position: number | null
  verifyFraming: boolean
  categories: string[]
  impact: Impact
  confidence: string
  confidenceReason: string
}

const dataBR = (iso: string) => iso.split('-').reverse().join('/')

const sha = dados.norma.sha256

export const demoNorm = {
  badge: 'Norma real · impacto ilustrativo',
  kind: 'Resolução Normativa ANEEL',
  number: 'nº 1.137/2025',
  issuer: 'ANEEL · Agência Nacional de Energia Elétrica',
  effective: dataBR(dados.norma.vigencia),
  extracted: dados.norma.obrigacoes_extraidas,
  prioritized: dados.norma.priorizadas,
  toVerify: dados.norma.verificar_enquadramento,
  subject: "Impacto e prazos para uma distribuidora ilustrativa, com cada estimativa ligada à fonte.",
  url: dados.norma.url,
  fingerprint: `sha256 ${sha.slice(0, 4)}…${sha.slice(-4)}`,
  sha256: sha,
  articles: dados.unidades.map((u) => ({ id: u.id, label: u.dispositivo, text: u.texto })) satisfies Article[],
}

export const changes: Change[] = dados.alertas.map((a) => ({
  id: a.id,
  title: a.titulo,
  detail: a.detalhe,
  effect: a.efeito_empresa,
  wording: a.redacao,
  articleId: a.unidade,
}))

export const obligations: Obligation[] = dados.obrigacoes.map((o) => ({
  id: o.id,
  short: o.titulo_curto,
  title: o.acao,
  subject: o.sujeito,
  articleId: o.unidade,
  anchor: o.trecho,
  deadline: o.prazo,
  deadlineDetail: o.prazo_detalhe,
  deadlineDate: o.data_prazo,
  pending: o.data_prazo ? undefined : 'A norma não traz prazo para esta obrigação. Nenhuma data é presumida.',
  position: o.posicao,
  verifyFraming: o.verificar_enquadramento,
  categories: o.categorias.map((c) => c.nome),
  impact: {
    min: o.impacto.minimo_reais,
    probable: (o.impacto.provavel_reais as { sem_teto: number } | null)?.sem_teto ?? null,
    probableReason: o.impacto.motivo_provavel,
    max: o.impacto.maximo_reais.sem_teto,
    maxPct: o.impacto.maximo_pct.sem_teto,
    groupCapPct: o.impacto.teto_grupo_pct,
    legalCapPct: o.impacto.teto_legal_pct,
    legalCapUnderestimated: o.impacto.teto_legal_subestimado,
    groups: o.impacto.grupos,
    framings: o.impacto.enquadramentos.map((f) => ({ ...f, ...fontes.infracoes_demo[f.dispositivo as keyof typeof fontes.infracoes_demo] })),
    premises: o.impacto.premissas,
    sources: o.impacto.fontes,
  },
  confidence: o.confianca,
  confidenceReason: o.motivo_confianca,
}))

export const profile = {
  label: dados.perfil.rotulo,
  notice: dados.perfil.aviso,
  base: dados.perfil.base_reais,
  baseOrigin: dados.perfil.origem_base,
  referenceDate: dataBR(dados.perfil.data_referencia),
}

export const notices = { estimate: dados.aviso, date: dados.aviso_data, order: dados.regra_ordem }

const reais = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
/** "R$ 100 milhões", "R$ 5 bilhões": leitura rápida para quem decide; o valor exato fica no JSON. */
export function brl(valor: number): string {
  if (valor >= 1e9) return `R$ ${(valor / 1e9).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} bilhões`
  if (valor >= 1e6) return `R$ ${(valor / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} milhões`
  return reais.format(valor)
}

export const pct = (v: number) => `${v.toLocaleString('pt-BR', { maximumFractionDigits: 3 })}%`

export const articleById = (id: string) => demoNorm.articles.find((a) => a.id === id)!

export const funnel = dados.funil
export const priorities = obligations.filter((o) => !o.verifyFraming).sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
export const unknownFraming = obligations.filter((o) => o.verifyFraming)
