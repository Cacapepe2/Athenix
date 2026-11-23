// Página executiva (/demo/executivo): três números, as 5 obrigações para olhar primeiro e a referência do
// setor, para QUALQUER norma processada pelo mesmo motor. Nada é digitado aqui: tudo vem dos planos
// gerados por `python -m athenix processar` (landing/src/content/plano-*.json). "Por infração" sempre:
// nunca soma valores de infrações diferentes. Linguagem de negócio: o grupo da REN 846 vira
// "infração grave (Grupo IV)" (mapeamento em gravidade.ts).
import {
  brlCurto, comAtenuantePct, contarVencidas, dataBR, HOJE, maximoPct, pct, planos, reaisDe, SIM_INICIAL,
  type Faixa, type Modo, type NormaId, type Obrigacao, type PlanoDados, type Simulacao,
} from './plano.ts'
import { GRUPOS, rotuloDoGrupo, nomeDaGravidade, type Grupo } from './gravidade.ts'
import { atualizar } from './datas.ts'

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

/** "Vencido desde 28/04/2026 (207 dias)" / "Vence em 04/11/2027 (348 dias)": prazo mais urgente do tema, contado de HOJE. */
export function textoPrazoDoTema(p: PlanoDados, t: { prazo_mais_urgente: { obrigacao: string; data: string | null; texto: string } | null }, hoje: string = HOJE): string {
  const u = t.prazo_mais_urgente
  if (!u) return 'Sem data no texto'
  const o = p.obrigacoes.find((x) => x.id === u.obrigacao)
  if (!o || !u.data) return u.texto
  const a = atualizar(o, hoje)
  return a.situacao === 'vencida' ? `Vencido desde ${dataBR(u.data)} (${Math.abs(a.prazo.dias!)} dias)` : `Vence em ${dataBR(u.data)} (${a.prazo.dias} dias)`
}

export interface Prazos {
  /** Obrigações principais vencidas (item ou dispositivo) e as alíneas de detalhe vencidas, à parte. */
  vencidas: number
  detalhes: number
  proxima: { dias: number; data: string } | null
  /** Próximo marco de transição com data futura: "03/05/2027 · adequação", "02/02/2027 · vigência". */
  proximoMarco: { data: string; tipo: 'adequação' | 'vigência' } | null
  /** "N em vigor desde 04/11/2026 · N condicionais · N recorrentes"; null sem marco de transição na norma. */
  contagem: { emVigor: number; desde: string | null; condicionais: number; recorrentes: number } | null
}

const TIPO_MARCO = { adequacao: 'adequação', vigencia: 'vigência' } as const
const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`

/** Cartão 3: obrigações vencidas, o próximo marco de transição e a próxima que vence (só prazos com data). */
export function prazos(p: PlanoDados, hoje: string = HOJE): Prazos {
  const obrig = p.obrigacoes.map((o) => atualizar(o, hoje))
  const futuras = obrig.filter((o) => (o.situacao === '90dias' || o.situacao === 'depois') && o.prazo.dias != null && o.prazo.data)
  const prox = futuras.length ? futuras.reduce((a, b) => (b.prazo.dias! < a.prazo.dias! ? b : a)) : null
  const marcos = obrig.flatMap((o) => (o.marco && (o.marco.tipo === 'adequacao' || o.marco.tipo === 'vigencia') && o.marco.data && o.marco.data > hoje ? [o.marco] : []))
  const pm = marcos.length ? marcos.reduce((a, b) => (b.data! < a.data! ? b : a)) : null
  const emVigor = obrig.filter((o) => o.marco?.tipo === 'em_vigor')
  return {
    ...(({ obrigacoes, detalhes }) => ({ vencidas: obrigacoes, detalhes }))(contarVencidas(obrig)),
    proxima: prox ? { dias: prox.prazo.dias!, data: prox.prazo.data! } : null,
    proximoMarco: pm ? { data: pm.data!, tipo: TIPO_MARCO[pm.tipo as 'adequacao' | 'vigencia'] } : null,
    contagem: obrig.some((o) => o.marco)
      ? { emVigor: emVigor.length, desde: emVigor[0]?.marco?.data ?? null, condicionais: obrig.filter((o) => o.prazo.condicional).length, recorrentes: obrig.filter((o) => o.situacao === 'recorrente').length }
      : null,
  }
}

/** "46 em vigor desde 04/11/2026 · 1 condicional · 2 recorrentes" (linha pequena do cartão 3). */
export function textoContagem(c: NonNullable<Prazos['contagem']>): string {
  const partes = [c.desde ? `${c.emVigor} em vigor desde ${dataBR(c.desde)}` : null, plural(c.condicionais, 'condicional', 'condicionais'), plural(c.recorrentes, 'recorrente', 'recorrentes')]
  return partes.filter(Boolean).join(' · ')
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

/** "contada de 30/10/2025 · provisória" (a data de partida que o motor leu no texto); null sem data. */
export function prazoBase(o: Obrigacao): string | null {
  return o.prazo.data && o.prazo.base ? `contada de ${dataBR(o.prazo.base)}${o.prazo.provisorio ? ' · provisória' : ''}` : null
}

/** Texto curto do prazo para os blocos: "vencida há 293 dias", "vence em 47 dias", "recorrente". */
export function prazoCurto(o: Obrigacao): string {
  return prazoTexto(o, false)
}

export function prazoTexto(o: Obrigacao, comBase = true): string {
  const d = o.prazo.dias
  const contada_ = comBase ? contada(o) : ''
  if (o.situacao === 'vencida' && d != null) return `vencida há ${Math.abs(d)} dias${contada_}`
  // Marco de transição com data futura: diz o que é ("adequação até 03/05/2027"), não só "vence em".
  if ((o.situacao === '90dias' || o.situacao === 'depois') && d != null && o.marco?.data === o.prazo.data && (o.marco.tipo === 'adequacao' || o.marco.tipo === 'vigencia'))
    return `${o.marco.tipo === 'adequacao' ? 'adequação até' : 'vigência a partir de'} ${dataBR(o.prazo.data!)} (em ${d} dias)`
  if ((o.situacao === '90dias' || o.situacao === 'depois') && d != null) return `vence em ${d} dias${contada_}`
  if (o.situacao === 'recorrente') return 'recorrente'
  if (o.prazo.condicional) return 'maior entre 12 meses e o prazo informado'
  if (o.situacao === 'evento') return 'depende de um evento'
  if (o.marco?.tipo === 'em_vigor' && o.marco.data) return `em vigor desde ${dataBR(o.marco.data)}`
  return 'sem prazo no texto'
}

/** "grave · até R$ 50 mi" (identificado); com etiqueta "preliminar" quando vem de sugestão da IA. Sem
 *  enquadramento: "a enquadrar · sem valor". */
export function textoDoValor(v: ValorExecutivo | null): { gravidade: string; valor: string; preliminar: string | null } {
  if (!v) return { gravidade: 'a enquadrar', valor: 'sem valor (sem enquadramento)', preliminar: null }
  const valor = v.reais != null ? `até ${brlCurto(v.reais)}` : `até ${pct(v.pct)} da receita`
  return { gravidade: nomeDaGravidade(v.grupo), valor, preliminar: v.origem === 'sugerido' ? 'preliminar' : null }
}

/** "O que recomendamos": a 1ª ação ESPECÍFICA do dispositivo (IA, validada, "Sugestão"). Sem ela, null:
 *  a tela diz "recomendação em revisão". Nunca frase genérica do manual do tipo no top 5. */
export function oQueFazer(_p: PlanoDados, o: Obrigacao): { texto: string; preliminar: boolean; todas: string[] } | null {
  const r = (o.recomendacoes ?? []).map((x) => x.acao)
  if (!r.length) return null
  return { texto: acaoGerencial(r), preliminar: true, todas: r }
}

/** Detalhe operacional (equipamento, ferramenta, ordem de campo): só o plano completo mostra. */
const OPERACIONAL = /motosserra|guincho|scada|equipes? de campo|caminh[ãa]o|ve[íi]culo|ferramenta|\bEPI\b|r[áa]dio|sensor|religador|disjuntor|transformador|poste|\bacione\b|imediatamente|checklist|rotina automatizada|script/i
const MAX_PALAVRAS_GERENCIAL = 22
export const eGerencial = (acao: string) => !OPERACIONAL.test(acao) && acao.split(/\s+/).length <= MAX_PALAVRAS_GERENCIAL

/** Ação para a executiva: a primeira de nível gerencial; sem nenhuma, a mais genérica (a mais curta) das válidas. */
export function acaoGerencial(acoes: string[]): string {
  return acoes.find(eGerencial) ?? [...acoes].sort((a, b) => a.split(/\s+/).length - b.split(/\s+/).length)[0]
}

/** Defesa possível: causa externa no texto (com citação), prática conhecida do tema (a avaliar) ou "—". */
export type OrigemDefesa = 'no texto' | 'marco do texto' | 'prática conhecida'

/** A "prática conhecida" só vale quando o dever É a ação que a dependência condiciona (poda para a autorização municipal;
 *  comunicação para os canais de terceiros). Mencionar a prefeitura ou o município no texto não basta. */
const ACAO_DA_PRATICA: Record<string, RegExp> = {
  autorizacao_municipal: /\b(?:poda\w*|podar|supress[ãa]o|corte de [áa]rvores?|remo[çc][ãa]o de (?:[áa]rvores?|vegeta[çc][ãa]o))\b/i,
  indisponibilidade_de_canais: /\b(?:comunic\w+|avis\w+|mensagens?|notific\w+|SMS|aplicativo|atendimento telef[ôo]nico)\b/i,
}

export function defesa(p: PlanoDados, o: Obrigacao): { texto: string; origem: OrigemDefesa | null } {
  // O marco está no texto (a norma conta o prazo da publicação de instruções da ANEEL); se elas já saíram, não se sabe daqui.
  if (o.analise?.dependencias_no_texto.some((d) => d.id === 'ato_da_aneel')) return { texto: 'verificar se as instruções da ANEEL foram publicadas', origem: 'marco do texto' }
  if (o.excludente) return { texto: 'excludente previsto no texto da norma', origem: 'no texto' }
  const texto = `${o.titulo_completo} ${o.trecho ?? ''}`
  const dep = p.analise.pratica_por_tema[o.tema]
  if (dep && ACAO_DA_PRATICA[dep]?.test(texto)) return { texto: simplificar(p.analise.dependencias[dep].nome).toLowerCase(), origem: 'prática conhecida' }
  const outra = p.analise.causas_por_tema[o.tema]
  if (outra && ACAO_DA_PRATICA.indisponibilidade_de_canais.test(texto)) return { texto: outra.nome.toLowerCase(), origem: 'prática conhecida' }
  return { texto: '—', origem: null }
}

export const urlPlanoCompleto = (id: NormaId) => (id === NORMA_PADRAO ? '/demo' : `/demo?norma=${id}`)
/** Abre o plano completo da norma já imprimindo o relatório de trabalho. */
export const urlRelatorio = (id: NormaId) => (id === NORMA_PADRAO ? '/demo?relatorio=1' : `/demo?norma=${id}&relatorio=1`)
export const idDaObrigacao = (id: string) => `obrigacao-${id}`
/** Abre a obrigação certa na página completa da norma. */
/** "Detalhes no plano": o plano da norma só com esta obrigação (?item=), aberta (#obrigacao-). */
export const urlDetalhe = (id: NormaId, obrigacaoId: string) => `${urlPlanoCompleto(id)}${id === NORMA_PADRAO ? '?' : '&'}item=${obrigacaoId}#${idDaObrigacao(obrigacaoId)}`

/** Título curto do bloco: o rótulo de até 5 palavras gerado por IA; sem ele, o título completo encurtado. */
export function tituloCurto(o: Obrigacao): string {
  return o.titulo_curto ?? frase(o, 40)
}

export interface BarraDeValor { rotulo: string; reais: number | null; pct: number; fracao: number; cor: 'teto' | 'media' | 'reducao' }

/** Três barras do painel: teto, atenuante do art. 24, II e do art. 24, I (valor por infração, nunca soma). */
export function barrasDeValor(p: PlanoDados, v: ValorExecutivo | null, s: Simulacao | null): BarraDeValor[] {
  if (!v) return []
  const base = s ?? SIM_INICIAL
  const med = (c: 'ate_tn' | 'espontanea') => p.reducao.medidas.find((m) => m.cenario === c)
  const rotuloArt = (c: 'ate_tn' | 'espontanea') => `art. ${(med(c)?.dispositivo ?? '').replace(/^Art\.\s*/, '')}`
  const por = (c: 'ate_tn' | 'espontanea') => {
    const r = med(c)?.percentual
    return comAtenuantePct(v.faixa, base, c) ?? (r != null ? v.pct * (1 - r / 100) : null)
  }
  const mk = (rotulo: string, pctV: number, cor: BarraDeValor['cor']): BarraDeValor => ({ rotulo, pct: pctV, reais: s ? reaisDe(pctV, s) : null, fracao: v.pct ? Math.min(pctV / v.pct, 1) : 0, cor })
  const ii = por('ate_tn')
  const i = por('espontanea')
  return [mk('teto', v.pct, 'teto'), ...(ii != null ? [mk(rotuloArt('ate_tn'), ii, 'media')] : []), ...(i != null ? [mk(rotuloArt('espontanea'), i, 'reducao')] : [])]
}

/** "Prove com": a primeira evidência do manual do tipo da obrigação (rascunho; marcada como sugestão). */
export function proveCom(p: PlanoDados, o: Obrigacao): string | null {
  const t = o.analise?.tipo
  const id = t?.id ?? t?.regra_id ?? null
  return (id && p.analise.manuais[id]?.evidencias[0]) || null
}

export interface LinhaTop5 {
  id: string
  sujeitoImplicito: boolean
  area: string
  areaOrigem: 'regra' | 'ia' | null
  dataPrazo: string | null
  /** Citação literal do dispositivo (o que a norma exige). */
  trecho: string | null
  /** Valor por infração se regularizar antes da fiscalização (atenuante do art. 24, I). */
  reduzidoReais: number | null
  situacaoPrazo: Obrigacao['situacao']
  titulo: string
  prazoCurto: string
  prazoBase: string | null
  barras: BarraDeValor[]
  proveCom: string | null
  evite: string | null
  gravidadeRotulo: string
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
  fazer: { texto: string; preliminar: boolean; todas: string[] } | null
  defesa: { texto: string; origem: OrigemDefesa | null }
  link: string
}

const VERBO = /^[A-ZÀ-Ú][a-zà-úç]+(?:ar|er|ir)\s/
const GRAU: Record<Obrigacao['situacao'], number> = { vencida: 0, '90dias': 1, depois: 2, recorrente: 3, evento: 4, sem_prazo: 4 }

/** As 5 obrigações para olhar primeiro: vencidas (a mais antiga antes) → em vigor sem adequação (já exigíveis)
 *  → próximos marcos e prazos com data (o mais próximo antes) → condicionais → o resto; dentro de cada grupo,
 *  maior valor por infração, depois enquadramento identificado no texto antes do sugerido. */
export function top5(normaId: NormaId, s: Simulacao | null, modo: Modo, n = 5, hoje: string = HOJE): LinhaTop5[] {
  const p = norma(normaId).dados
  // Situação e dias recalculados para HOJE (o JSON traz os da data de referência da geração).
  const comValor = p.obrigacoes.map((o, i) => { const a = atualizar(o, hoje); return { o: a, i, v: valorDaObrigacao(a, s, modo) } })
  // Grupo: 0 vencidas, 1 em vigor sem adequação, 2 a vencer com data (marcos), 3 condicionais, 4 o resto.
  // Nas vencidas e nas com data, a data mais próxima antes.
  const grupo = (o: Obrigacao) =>
    o.situacao === 'vencida' ? 0
      : o.marco?.tipo === 'em_vigor' && o.situacao === 'sem_prazo' ? 1
        : o.prazo.data && (o.situacao === '90dias' || o.situacao === 'depois') ? 2
          : o.prazo.condicional ? 3 : 4
  comValor.sort((a, b) => {
    const ga = grupo(a.o)
    const gb = grupo(b.o)
    if (ga !== gb) return ga - gb
    if ((ga === 0 || ga === 2) && a.o.prazo.data !== b.o.prazo.data) return (a.o.prazo.data ?? '') < (b.o.prazo.data ?? '') ? -1 : 1
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
      id: o.id, sujeitoImplicito: o.sujeito_implicito, area: o.area, areaOrigem: o.area_origem, dataPrazo: o.prazo.data, trecho: o.trecho, situacaoPrazo: o.situacao, reduzidoReais: barrasDeValor(p, v, s).find((b) => b.cor === 'reducao')?.reais ?? null, titulo: tituloCurto(o), prazoCurto: prazoCurto(o), prazoBase: prazoBase(o), barras: barrasDeValor(p, v, s),
      proveCom: proveCom(p, o), evite: o.evite?.acao ?? null, gravidadeRotulo: rotuloDoGrupo(v?.grupo), normaId, frase: frase(o), fraseOriginal: o.titulo_completo, dispositivo: o.dispositivo,
      prazo: prazoTexto(o), situacao: o.situacao, valor: v, gravidade: t.gravidade, textoValor: t.valor,
      preliminar: t.preliminar, fazer: oQueFazer(p, o), defesa: defesa(p, o), link: urlDetalhe(normaId, o.id),
    }
  })
}

export interface ReferenciaSetor { texto: string; n: number; mediana: number; maximo: number; usouGeral: boolean; nota: string; maiorMulta: string }

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
    maiorMulta: textoMaiorMulta(p),
  }
}

/** "maior multa já aplicada a uma distribuidora: R$ 165,8 mi (2024), por falhas no restabelecimento após evento climático" (informado; sem nome de empresa). */
export function textoMaiorMulta(p: PlanoDados): string {
  const m = p.referencia_escala.maior_multa
  return `${m.rotulo}: ${brlCurto(m.valor_reais)}`
}

export interface DestaqueDaNorma { texto: string; rotuloData: string; data: string; deveres: number; comPrazo: number; recorrentes: number }

/** Destaque da norma: "publicada em 04/11/2026 · 86 deveres identificados · 5 com prazo · 2 recorrentes". Tudo dos dados. */
export function destaqueDaNorma(p: PlanoDados): DestaqueDaNorma {
  const deveres = p.resumo.aplicaveis
  const comPrazo = p.obrigacoes.filter((o) => o.prazo.data).length
  const recorrentes = p.obrigacoes.filter((o) => o.situacao === 'recorrente').length
  const rotuloData = p.norma.data_rotulo
  const rec = `${recorrentes} ${recorrentes === 1 ? 'recorrente' : 'recorrentes'}`
  return { texto: `${rotuloData} ${dataBR(p.norma.vigencia)} · ${deveres} deveres identificados · ${comPrazo} com prazo · ${rec}`, rotuloData, data: p.norma.vigencia, deveres, comPrazo, recorrentes }
}

export interface ContagemEnquadramentos { identificados: number; sugeridos: number; texto: string }

/** "X enquadramentos identificados no texto · Y sugeridos pela IA, aguardando revisão": contagem por obrigação. */
export function contagemDeEnquadramentos(p: PlanoDados): ContagemEnquadramentos {
  const identificados = p.obrigacoes.filter((o) => o.faixa).length
  const sugeridos = p.obrigacoes.filter((o) => !o.faixa && o.faixa_preliminar).length
  return { identificados, sugeridos, texto: `${plural(identificados, 'enquadramento identificado', 'enquadramentos identificados')} no texto · ${plural(sugeridos, 'sugerido', 'sugeridos')} pela IA, aguardando revisão` }
}

export interface LinhaGrupo { sha256: string; grupo: Grupo; nome: string; rotulo: string; pct: number | null; dispositivo: string | null; trecho: string | null }

/** Tabela "Como calculamos": teto de cada grupo e o teto legal, com a citação de cada um. */
export function tabelaDeGrupos(p: PlanoDados): { grupos: LinhaGrupo[]; tetoLegal: { pct: number | null; dispositivo: string; trecho: string; sha256: string } | null } {
  const grupos = GRUPOS.map((g) => {
    const e = p.escala_de_gravidade[`limite_grupo_${g}`]
    return { sha256: e?.sha256 ?? '', grupo: g, nome: nomeDaGravidade(g), rotulo: rotuloDoGrupo(g), pct: e?.percentual ?? null, dispositivo: e?.dispositivo ?? null, trecho: e?.trecho ?? null }
  })
  const t = p.escala_de_gravidade.teto_legal_lei
  return { grupos, tetoLegal: t ? { pct: t.percentual, dispositivo: t.dispositivo, trecho: t.trecho, sha256: t.sha256 } : null }
}
