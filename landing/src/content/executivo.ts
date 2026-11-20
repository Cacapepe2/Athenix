// Página executiva (/demo/executivo): três números, as 5 obrigações para olhar primeiro e a referência do
// setor, para QUALQUER norma processada pelo mesmo motor. Nada é digitado aqui: tudo vem dos planos
// gerados por `python -m athenix processar` (landing/src/content/plano-*.json). "Por infração" sempre:
// nunca soma valores de infrações diferentes. Linguagem de negócio: o grupo da REN 846 vira
// "infração grave (Grupo IV)" (mapeamento em gravidade.ts).
import {
  brlCurto, comAtenuantePct, dataBR, maximoPct, pct, planos, reaisDe, SIM_INICIAL,
  type Faixa, type Modo, type NormaId, type Obrigacao, type PlanoDados, type Simulacao,
} from './plano.ts'
import { GRUPOS, rotuloDoGrupo, nomeDaGravidade, type Grupo } from './gravidade.ts'

export const NORMAS: { id: NormaId; rotulo: string; resumo: string; dados: PlanoDados }[] = [
  { id: 'rn1137', rotulo: 'RN 1.137/2025', resumo: 'eventos climáticos extremos', dados: planos.rn1137 },
  { id: 'ren1174', rotulo: 'REN 1.174/2026', resumo: 'abertura do mercado livre de energia', dados: planos.ren1174 },
]
export const NORMA_PADRAO: NormaId = 'rn1137'
export const norma = (id: NormaId) => NORMAS.find((n) => n.id === id)!

/** Menos autos que isto e a referência por infração grave não é usada (cai para a referência geral). */
export const MIN_AUTOS_REFERENCIA = 5

export type OrigemValor = 'identificado' | 'sugerido'
const RANK_ORIGEM: Record<OrigemValor, number> = { identificado: 0, sugerido: 1 }

export interface ValorExecutivo {
  /** Máximo por infração em % da receita (limitado pelo teto legal); nunca a soma de infrações. */
  pct: number
  reais: number | null
  origem: OrigemValor
  /** Grupo da REN 846 (I a V): o do enquadramento identificado no texto ou o sugerido pela IA. */
  grupo: string
  faixa: Faixa
}

const maisGrave = (gs: string[]) => [...gs].sort((a, b) => GRUPOS.indexOf(b as Grupo) - GRUPOS.indexOf(a as Grupo))[0]

/** Valor por infração de uma obrigação: identificado no texto; senão sugerido pela IA (só no cenário
 *  preliminar); senão NENHUM: sem enquadramento não há valor (nada de "pior caso" da escala). */
export function valorDaObrigacao(o: Obrigacao, s: Simulacao | null, modo: Modo): ValorExecutivo | null {
  const base = s ?? SIM_INICIAL
  let c: { f: Faixa; origem: OrigemValor; grupo: string } | null = null
  if (o.faixa) c = { f: o.faixa, origem: 'identificado', grupo: o.grupo ?? maisGrave(o.faixa.grupos) }
  else if (modo === 'preliminar' && o.faixa_preliminar) c = { f: o.faixa_preliminar, origem: 'sugerido', grupo: o.ia?.grupo ?? maisGrave(o.faixa_preliminar.grupos) }
  if (!c) return null
  const p = maximoPct(c.f, base)
  return { pct: p, reais: s ? reaisDe(p, s) : null, origem: c.origem, grupo: c.grupo, faixa: c.f }
}

const melhor = (a: ValorExecutivo | null, b: ValorExecutivo | null) => {
  if (!a) return b
  if (!b) return a
  if (b.pct !== a.pct) return b.pct > a.pct ? b : a
  return RANK_ORIGEM[b.origem] < RANK_ORIGEM[a.origem] ? b : a
}

/** Cartão 1: o MAIOR valor por infração do plano (não é soma). Sem nenhum enquadramento, null. */
export function valorGeral(p: PlanoDados, s: Simulacao | null, modo: Modo): ValorExecutivo | null {
  return p.obrigacoes.reduce<ValorExecutivo | null>((m, o) => melhor(m, valorDaObrigacao(o, s, modo)), null)
}

export interface Queda { de: number | null; para: number | null; reducaoPct: number; dispositivo: string; trecho: string; fonte: string; sha256: string }

/** Cartão 2: quanto cai se cessar a infração e reparar o dano antes da fiscalização (atenuante do art. 24, I da REN 846). */
export function queda(p: PlanoDados, s: Simulacao | null, modo: Modo): Queda | null {
  const v = valorGeral(p, s, modo)
  const m = p.reducao.medidas.find((x) => x.cenario === 'espontanea')
  if (!v || !m || m.percentual == null) return null
  const base = s ?? SIM_INICIAL
  const aten = comAtenuantePct(v.faixa, base, 'espontanea') ?? v.pct * (1 - m.percentual / 100)
  return { de: v.reais, para: s ? reaisDe(aten, s) : null, reducaoPct: m.percentual, dispositivo: m.dispositivo, trecho: m.trecho, fonte: m.fonte, sha256: m.sha256 }
}

export interface Prazos { vencidas: number; proxima: { dias: number; data: string } | null }

/** Cartão 3: obrigações vencidas e a próxima que vence (só prazos com data). */
export function prazos(p: PlanoDados): Prazos {
  const futuras = p.obrigacoes.filter((o) => (o.situacao === '90dias' || o.situacao === 'depois') && o.prazo.dias != null && o.prazo.data)
  const prox = futuras.length ? futuras.reduce((a, b) => (b.prazo.dias! < a.prazo.dias! ? b : a)) : null
  return { vencidas: p.resumo.por_situacao.vencida, proxima: prox ? { dias: prox.prazo.dias!, data: prox.prazo.data! } : null }
}

// ---------- linguagem de negócio ----------

const SIGLAS: [RegExp, string][] = [
  [/\bDISE\b/, 'DISE (duração da interrupção em situação de emergência)'],
  [/\bCCEE\b/, 'CCEE (câmara que contabiliza o mercado de energia)'],
  [/\bACL\b/, 'mercado livre (ACL)'],
  [/\bACR\b/, 'mercado regulado (ACR)'],
  [/\bCCER\b/, 'contrato de energia do consumidor (CCER)'],
  [/\bROL\b/, 'receita operacional líquida'],
  [/\bTN\b/, 'Termo de Notificação'],
  [/subgrupo AS ou A4/i, 'subgrupo AS ou A4 (alta tensão)'],
  [/\bREN 846\b/, 'REN 846 (regulamento de multas da ANEEL)'],
]

/** Troca o jargão por linguagem simples (a frase original da norma fica no detalhe). */
export function simplificar(texto: string): string {
  let t = texto.replace(/\s+/g, ' ').trim()
  t = t.replace(/\bdisponibilizar\s+(?:em|no)\s+s[ií]tio eletr[ôo]nico(?:\s+na internet)?/gi, 'publicar no site')
  t = t.replace(/\bs[ií]tio eletr[ôo]nico(?:\s+na internet)?/gi, 'site')
  t = t.replace(/\bdisponibilizar\b/gi, 'publicar')
  t = t.replace(/\bpostos de atendimento presencial\b/gi, 'postos de atendimento')
  for (const [re, nova] of SIGLAS) {
    const i = t.search(re)
    if (i >= 0) t = t.slice(0, i) + t.slice(i).replace(re, nova)
  }
  return t.charAt(0).toUpperCase() + t.slice(1)
}

const FINAIS_FRACOS = /\s+(?:de|da|do|das|dos|e|em|no|na|nos|nas|que|para|por|com|a|o|as|os|ao|à)$/i

/** Frase curta (até `max` caracteres), sem reticências nem palavra cortada; o texto inteiro está no detalhe. */
export function frase(o: Obrigacao, max = 110): string {
  const completo = simplificar(o.titulo_completo)
  let corte = completo.length <= max ? completo : completo.slice(0, max).replace(/\s+\S*$/, '')
  corte = corte.replace(/[,;:\s]+$/, '').replace(/[;,]\s+(?:e|ou)$/i, '')
  while (FINAIS_FRACOS.test(corte)) corte = corte.replace(FINAIS_FRACOS, '')
  return corte.replace(/[,;:\s]+$/, '')
}

/** "contada de 12/08/2026": de onde vem a data provisória (o marco que o motor leu no texto). */
const contada = (o: Obrigacao) => (o.prazo.provisorio && o.prazo.base ? ` (provisória, contada de ${dataBR(o.prazo.base)})` : '')

export function prazoTexto(o: Obrigacao): string {
  const d = o.prazo.dias
  if (o.situacao === 'vencida' && d != null) return `vencida há ${Math.abs(d)} dias${contada(o)}`
  if ((o.situacao === '90dias' || o.situacao === 'depois') && d != null) return `vence em ${d} dias${contada(o)}`
  if (o.situacao === 'recorrente') return 'recorrente'
  if (o.situacao === 'evento') return 'depende de um evento'
  return 'sem prazo no texto'
}

/** "grave · até R$ 50 mi" (identificado); com etiqueta "preliminar" quando vem de sugestão da IA. Sem
 *  enquadramento: "a enquadrar · sem valor". */
export function textoDoValor(v: ValorExecutivo | null): { gravidade: string; valor: string; preliminar: string | null } {
  if (!v) return { gravidade: 'a enquadrar', valor: 'sem valor (sem enquadramento)', preliminar: null }
  const valor = v.reais != null ? `até ${brlCurto(v.reais)}` : `até ${pct(v.pct)} da receita`
  return { gravidade: nomeDaGravidade(v.grupo), valor, preliminar: v.origem === 'sugerido' ? 'preliminar' : null }
}

export function oQueFazer(p: PlanoDados, o: Obrigacao): { texto: string; preliminar: boolean } | null {
  const t = o.analise?.tipo
  const id = t?.id ?? t?.regra_id ?? null
  const manual = id ? p.analise.manuais[id] : undefined
  if (!manual) return null
  return { texto: manual.ideias_cumprimento[0], preliminar: t?.situacao !== 'concordam' }
}

/** Defesa possível: causa externa no texto (com citação), prática conhecida do tema (a avaliar) ou "—". */
export function defesa(p: PlanoDados, o: Obrigacao): { texto: string; origem: 'no texto' | 'prática conhecida' | null } {
  if (o.analise?.dependencias_no_texto.some((d) => d.id === 'ato_da_aneel')) return { texto: 'instruções da ANEEL ainda por publicar', origem: 'no texto' }
  if (o.excludente) return { texto: 'excludente previsto no texto da norma', origem: 'no texto' }
  const dep = p.analise.pratica_por_tema[o.tema]
  if (dep) return { texto: simplificar(p.analise.dependencias[dep].nome).toLowerCase(), origem: 'prática conhecida' }
  const outra = p.analise.causas_por_tema[o.tema]
  if (outra) return { texto: outra.nome.toLowerCase(), origem: 'prática conhecida' }
  return { texto: '—', origem: null }
}

export const urlPlanoCompleto = (id: NormaId) => (id === NORMA_PADRAO ? '/demo' : `/demo?norma=${id}`)
export const idDaObrigacao = (id: string) => `obrigacao-${id}`
/** Abre a obrigação certa na página completa da norma. */
export const urlDetalhe = (id: NormaId, obrigacaoId: string) => `${urlPlanoCompleto(id)}#${idDaObrigacao(obrigacaoId)}`

export interface LinhaTop5 {
  id: string
  normaId: NormaId
  frase: string
  fraseOriginal: string
  dispositivo: string | null
  prazo: string
  situacao: Obrigacao['situacao']
  valor: ValorExecutivo | null
  gravidade: string
  textoValor: string
  preliminar: string | null
  fazer: { texto: string; preliminar: boolean } | null
  defesa: { texto: string; origem: 'no texto' | 'prática conhecida' | null }
  link: string
}

const VERBO = /^[A-ZÀ-Ú][a-zà-úç]+(?:ar|er|ir)\s/
const GRAU: Record<Obrigacao['situacao'], number> = { vencida: 0, '90dias': 1, depois: 2, recorrente: 3, evento: 4, sem_prazo: 4 }

/** As 5 obrigações para olhar primeiro: vencidas (a mais antiga antes), depois maior valor por infração,
 *  depois enquadramento identificado no texto antes do sugerido. */
export function top5(normaId: NormaId, s: Simulacao | null, modo: Modo, n = 5): LinhaTop5[] {
  const p = norma(normaId).dados
  const comValor = p.obrigacoes.map((o, i) => ({ o, i, v: valorDaObrigacao(o, s, modo) }))
  comValor.sort((a, b) => {
    const va = a.o.situacao === 'vencida' ? 0 : 1
    const vb = b.o.situacao === 'vencida' ? 0 : 1
    if (va !== vb) return va - vb
    if (va === 0 && a.o.prazo.data !== b.o.prazo.data) return (a.o.prazo.data ?? '') < (b.o.prazo.data ?? '') ? -1 : 1
    const pa = a.v?.pct ?? -1
    const pb = b.v?.pct ?? -1
    if (pa !== pb) return pb - pa
    const ra = a.v ? RANK_ORIGEM[a.v.origem] : 9
    const rb = b.v ? RANK_ORIGEM[b.v.origem] : 9
    if (ra !== rb) return ra - rb
    const va2 = VERBO.test(a.o.titulo) ? 0 : 1 // frase que começa por verbo no infinitivo é mais clara
    const vb2 = VERBO.test(b.o.titulo) ? 0 : 1
    if (va2 !== vb2) return va2 - vb2
    if (GRAU[a.o.situacao] !== GRAU[b.o.situacao]) return GRAU[a.o.situacao] - GRAU[b.o.situacao]
    return a.i - b.i
  })
  return comValor.slice(0, n).map(({ o, v }) => {
    const t = textoDoValor(v)
    return {
      id: o.id, normaId, frase: frase(o), fraseOriginal: o.titulo_completo, dispositivo: o.dispositivo,
      prazo: prazoTexto(o), situacao: o.situacao, valor: v, gravidade: t.gravidade, textoValor: t.valor,
      preliminar: t.preliminar, fazer: oQueFazer(p, o), defesa: defesa(p, o), link: urlDetalhe(normaId, o.id),
    }
  })
}

export interface ReferenciaSetor { texto: string; n: number; mediana: number; maximo: number; usouGeral: boolean; nota: string }

/** Linha "referência do setor": se o grupo do valor mostrado é o IV (infração grave) e há autos
 *  suficientes (n >= 5), a referência por infração grave (n = 10); em qualquer outro caso, a geral (n = 21). */
export function referenciaDoSetor(p: PlanoDados, grupo?: string | null): ReferenciaSetor {
  const g = p.referencia_escala.infracao_grave
  const geral = p.referencia_escala
  const grave = grupo === 'IV' && g.autos >= MIN_AUTOS_REFERENCIA
  const r = grave ? g : geral
  const quais = grave ? `autos de infração reais em distribuição com ${rotuloDoGrupo('IV')}` : 'autos de infração reais em distribuição (qualquer gravidade)'
  return {
    texto: `${quais}: mediana ≈ ${brlCurto(r.mediana_reais)}, maior ≈ ${brlCurto(r.maximo_reais)} (n = ${r.autos})`,
    n: r.autos, mediana: r.mediana_reais, maximo: r.maximo_reais, usouGeral: !grave,
    nota: 'valor do auto inteiro, não estimativa por obrigação',
  }
}

export interface DestaqueDaNorma { texto: string; rotuloData: string; data: string; deveres: number; comPrazo: number }

/** Destaque da norma: "publicada em 04/11/2026 · 91 deveres identificados · 3 com prazo". Tudo dos dados. */
export function destaqueDaNorma(p: PlanoDados): DestaqueDaNorma {
  const deveres = p.resumo.aplicaveis
  const comPrazo = p.obrigacoes.filter((o) => o.prazo.data).length
  const rotuloData = p.norma.data_rotulo
  return { texto: `${rotuloData} ${dataBR(p.norma.vigencia)} · ${deveres} deveres identificados · ${comPrazo} com prazo`, rotuloData, data: p.norma.vigencia, deveres, comPrazo }
}

export interface LinhaGrupo { grupo: Grupo; nome: string; rotulo: string; pct: number | null; dispositivo: string | null; trecho: string | null }

/** Tabela "Como calculamos": teto de cada grupo e o teto legal, com a citação de cada um. */
export function tabelaDeGrupos(p: PlanoDados): { grupos: LinhaGrupo[]; tetoLegal: { pct: number | null; dispositivo: string; trecho: string } | null } {
  const grupos = GRUPOS.map((g) => {
    const e = p.escala_de_gravidade[`limite_grupo_${g}`]
    return { grupo: g, nome: nomeDaGravidade(g), rotulo: rotuloDoGrupo(g), pct: e?.percentual ?? null, dispositivo: e?.dispositivo ?? null, trecho: e?.trecho ?? null }
  })
  const t = p.escala_de_gravidade.teto_legal_lei
  return { grupos, tetoLegal: t ? { pct: t.percentual, dispositivo: t.dispositivo, trecho: t.trecho } : null }
}
