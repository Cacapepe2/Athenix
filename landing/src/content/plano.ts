// Plano de ação da RN ANEEL 1.137/2025 para uma distribuidora ilustrativa. Dados gerados por
// scripts/exportar_plano_demo.py a partir do produto (athenix/plano.py): nenhum número é digitado aqui.
// Interpretações da IA vêm de um cache revisável, aparecem marcadas e nunca entram no cálculo.
import dados1137 from './plano-rn1137.json' with { type: 'json' }
import dados1174 from './plano-ren1174.json' with { type: 'json' }
import { hojeISO } from './datas.ts'
import { planoEm } from './referencia.ts'

export interface Marco {
  tipo: 'adequacao' | 'vigencia' | 'em_vigor' | 'a_confirmar'
  data: string | null
  /** Regra de transição da norma que dá o marco ("Art. 16, II, b") e o seu texto. */
  dispositivo: string | null
  trecho: string | null
  /** "Até a adequação, valem as regras anteriores" (caput da regra de adequação), quando a norma diz isso. */
  nota: string | null
  candidatos: string[] | null
}

export type Situacao = 'vencida' | '90dias' | 'depois' | 'recorrente' | 'evento' | 'sem_prazo'
export type Diagnostico = 'sim' | 'parcial' | 'nao'
export type Diagnosticos = Partial<Record<string, Diagnostico>>

export interface Faixa {
  grupos: string[]
  teto_grupo_pct: number
  maximo_pct: { com_teto: number; sem_teto: number }
  teto_legal_pct: number | null
  teto_legal_lei_pct: number | null
  teto_legal_subestimado: boolean | null
  maximo_reais?: { com_teto: number; sem_teto: number }
  /** % da base calculado pelo motor com o atenuante (valor base no teto do grupo, sem agravantes). */
  com_atenuante_pct: Partial<Record<Cenario, number>>
  com_atenuante_reais?: Partial<Record<Cenario, number>>
}

export type Cenario = 'espontanea' | 'ate_tn'

export interface Citacao {
  parametro: string
  dispositivo: string
  trecho: string
  percentual: number | null
  fonte: string
  sha256: string
}

export interface Medida extends Citacao {
  nome: string
  condicao: string
  efeito: string
  cenario: Cenario | null
}

export interface Obrigacao {
  id: string
  titulo: string
  titulo_origem: 'regra' | 'ia'
  /** Rótulo de até 5 palavras (IA, linguagem simples); null: usa o título encurtado. */
  titulo_curto: string | null
  /** Dever contado para a distribuidora sem ela escrita no texto (nem no caput): "sujeito implícito (a revisar)". */
  sujeito_implicito: boolean
  /** Área responsável SUGERIDA (data/areas_por_tipo.json): quem faz o quê. */
  area: string
  /** "regra": tipo achado pela regra; "ia": tipo sugerido pela IA (área sugerida (IA)); null: A definir. */
  area_origem: 'regra' | 'ia' | null
  /** "Evite" sugerido pela IA (cita trecho do dispositivo); null: a tela não mostra a linha. */
  evite: { acao: string; trecho_citado: string } | null
  /** Ações específicas sugeridas pela IA para este dispositivo (cada uma cita uma expressão literal dele). */
  recomendacoes: { acao: string; trecho_citado: string }[]
  /** Caput do inciso ou parágrafo (até 300 caracteres); vazio quando o dispositivo é o próprio caput. */
  contexto: string
  /** Título sem corte (o curto termina em "…" quando passa de 88 caracteres). */
  titulo_completo: string
  tema: string
  motivo_tema: string
  unidade: string | null
  dispositivo: string | null
  trecho: string | null
  situacao: Situacao
  prazo: { data: string | null; texto: string; dias: number | null; provisorio: boolean; base?: string | null; /** "o maior entre 12 meses da publicação e o prazo informado": sem data única. */ condicional?: boolean }
  /** Marco de vigência/transição lido da própria norma (athenix/vigencia.py): prazo de adequação, vigência
   *  diferida, "em vigor desde a publicação" ou ligação "a confirmar". Ausente em JSON antigo. */
  marco?: Marco | null
  calculo: 'fila' | 'verificar' | 'sem_multa'
  posicao_fila: number | null
  enquadramento: { dispositivo: string; grupo: string }[]
  ia: { dispositivo: string; grupo: string; justificativa: string; duvida: string | null } | null
  grupo: string | null
  faixa: Faixa | null
  /** Faixa do grupo SUGERIDO pela IA (aguarda confirmação); só entra no "cenário preliminar". */
  faixa_preliminar: Faixa | null
  analise?: AnaliseObrigacao
  premissas: string[]
  motivo_sem_calculo: string | null
  evidencias: { id: string; trecho: string }[]
  guardar: string[]
  excludente: string | null
}

export interface FonteDoc { titulo: string; arquivo: string; sha256: string }
export interface Infracao {
  grupo: string
  trecho: string
  origem_da_redacao: string
  fonte: FonteDoc
  /** O export relê a fonte versionada e confere o trecho literal. */
  conferido_na_fonte: boolean
}
export interface OutroDispositivo {
  id: string
  natureza: 'faculdade' | 'direito_de_terceiro' | 'competencia_aneel' | 'dever_de_outro_agente' | 'regra_de_transicao' | 'sem_dever_identificado'
  rotulo: string
  sujeito: string
  unidade: string | null
  dispositivo: string | null
  trecho: string | null
  motivo: string
}
export interface Sucessao {
  dispositivo: string
  duvida: string
  texto_da_duvida: string
  redacoes: { ato: string; vigencia_de: string; vigencia_ate: string | null; trecho: string; fonte: FonteDoc; estado: 'verified' | 'incerta'; conferido_na_fonte: boolean; motivo: string | null }[]
}

export type SituacaoTipo = 'so_regra' | 'concordam' | 'a_revisar' | 'sem_tipo'
export interface AnaliseObrigacao {
  tipo: { id: string | null; nome: string | null; situacao: SituacaoTipo; por: string; /** Tipo da regra, mesmo quando regra e IA ainda não concordam. */ regra_id: string | null }
  dependencias_no_texto: { id: string; trecho_literal: string }[]
}
export interface ManualDependencia {
  id: string
  nome: string
  o_que_guardar: string[]
  caminho: string
  cautela: string
  status: string
  precedentes: { id: string; titulo: string; urls: string[]; o_que_e: string; a_confirmar: string }[]
}

export interface Tema {
  id: string
  nome: string
  fontes: { rotulo: string; titulo: string; unidade: string }[]
  n: number
  contagem: Record<Situacao, number>
  prazo_mais_urgente: { obrigacao: string; data: string | null; texto: string; dias: number | null; situacao: Situacao } | null
  na_fila: number
  a_confirmar: number
  grupos: string[]
  grupo_mais_grave: string | null
  infracoes: string[]
  faixa: Faixa | null
  faixa_preliminar: Faixa | null
  grupos_sugeridos: string[]
  dependencias_no_texto: { obrigacao: string; id: string; trecho_literal: string }[]
  ia: { dispositivo: string; n: number; de: number } | null
  evidencias: { id: string; n: number; exemplo: { obrigacao: string; trecho: string } }[]
  principais: string[]
  obrigacoes: string[]
  guardar: { id: string; n: number }[]
  excludentes: { obrigacao: string; trecho: string }[]
  causa_externa: string | null
}

export interface PlanoDados {
  gerado_por: string
  commit_origem: string
  gerado_em: string
  aviso: string
  norma: { titulo: string; url: string | null; data_rotulo: string; sha256: string; vigencia: string }
  perfil: { rotulo: string; aviso: string; base_reais: number; origem_base: string; data_referencia: string }
  ia: { aviso: string; modelo: string; reasoning: string; criterio_titulos: string; criterio_enquadramentos: string } | null
  resumo: {
    identificadas: number
    /** Itens que não são deveres da distribuidora (seção "Outros dispositivos relevantes"). */
    outros_dispositivos: number
    aplicaveis: number
    fora_do_perfil: number
    por_situacao: Record<Situacao, number>
    na_fila: number
    a_confirmar: number
    sem_multa: number
    grupo_mais_grave: string | null
    temas: number
  }
  decisoes: { principais: unknown[]; confirmar: { obrigacoes: number; temas_sem_calculo_confirmado: number } }
  temas: Tema[]
  ordem_inicial: string[]
  obrigacoes: Obrigacao[]
  infracoes: Record<string, Infracao>
  /** Faculdades, direitos de terceiros e competências da ANEEL: fora da contagem de deveres. */
  outros_dispositivos: OutroDispositivo[]
  /** Unidades lidas sem marcador de dever e sem a distribuidora agindo: nada some em silêncio (motivo: "sem dever identificado"). */
  sem_dever_identificado: OutroDispositivo[]
  /** Redações datadas de um mesmo dispositivo (hoje o art. 11, XXIII), com fonte e estado. */
  sucessao_no_tempo: Sucessao[]
  linha_do_tempo: Record<Situacao, string[]>
  nomes_situacao: Record<Situacao, string>
  regra_ordem: string
  evidencias: Record<string, string>
  reducao: { rotulo: string; regras: Citacao[]; medidas: Medida[]; causa_externa: string }
  guardar: Record<string, string>
  /** Teto de cada grupo da REN 846 (art. 8º) e teto legal, com trecho, fonte e SHA-256. */
  escala_de_gravidade: Record<string, { dispositivo: string; trecho: string; percentual: number | null; fonte: string; sha256: string }>
  analise: {
    rotulo: string
    tipo_so_regra: string
    tipo_a_revisar: string
    areas: { rotulo: string; lista: string[] }
  manuais: Record<string, { nome: string; ideias_cumprimento: string[]; evidencias: string[]; status: string }>
    dependencias: Record<string, ManualDependencia>
    pratica_por_tema: Record<string, string>
    causas_por_tema: Record<string, { nome: string; nota: string }>
    contraponto: { titulo: string; urls: string[]; o_que_e: string; a_confirmar: string }
  }
  /** Nota por artigo em "Outros dispositivos relevantes" (ex.: Art. 12 da REN 1.174, grupo de trabalho). */
  notas_outros: Record<string, string>
  referencia_escala: { maior_multa: { rotulo: string; valor_reais: number; ano: number; motivo: string; fonte: string }; infracao_grave: { rotulo: string; autos: number; mediana_reais: number; maximo_reais: number; fonte: string; limites: string }; rotulo: string; segmento: string; unidade: string; autos: number; empresas: number; mediana_reais: number; maximo_reais: number; fonte: string; limites: string }
  simulador: {
    faixas: { id: string; rotulo: string; base: number }[]
    origem_faixas: string
    conferencia: { base: number; faturamento: number | null; obrigacao: string; maximo_reais: number; com_atenuante_reais: Partial<Record<Cenario, number>> }[]
  }
}

/** Os dois planos, gerados pelo mesmo comando (python -m athenix processar). */
/** A data de referência desta renderização (uma só): situação, dias e textos de prazo são recalculados a partir dela. */
export const HOJE = hojeISO()
export const planos = { rn1137: planoEm(dados1137 as unknown as PlanoDados, HOJE), ren1174: planoEm(dados1174 as unknown as PlanoDados, HOJE) }
export type NormaId = keyof typeof planos
/** Norma da página completa: ?norma=ren1174 na URL do navegador; sem parâmetro (e no build), a RN 1.137. */
export function normaDaUrl(): NormaId {
  try {
    const n = typeof location !== 'undefined' ? new URLSearchParams(location.search).get('norma') : null
    return n && Object.hasOwn(planos, n) ? (n as NormaId) : 'rn1137'
  } catch {
    return 'rn1137'
  }
}
export const plano: PlanoDados = planos[normaDaUrl()]

export const obrigacaoPorId = new Map(plano.obrigacoes.map((o) => [o.id, o]))
export const obrigacao = (id: string) => obrigacaoPorId.get(id)!

export const SITUACOES: Situacao[] = ['vencida', '90dias', 'depois', 'recorrente', 'evento', 'sem_prazo']
// Mesma regra de athenix/plano.py (ordenar_temas); o teste compara com plano.ordem_inicial.
const DEGRAU: Record<Situacao, number> = { vencida: 0, '90dias': 1, depois: 2, recorrente: 3, evento: 4, sem_prazo: 4 }

/** "preliminar": inclui as sugestões da IA (aguardam confirmação); "confirmados": só o que o texto da obrigação nomeia. */
export type Modo = 'preliminar' | 'confirmados'
export interface Exposicao {
  /** Máximo por infração em % da base (a maior das infrações do tema; nunca a soma). */
  pct: number
  reais: number | null
  origem: 'confirmado' | 'sugerido'
  faixa: Faixa
}

/** Exposição máxima por infração do tema no porte simulado. Sem enquadramento (nem sugerido): null. */
export function exposicaoTema(t: Tema, s: Simulacao | null, modo: Modo = 'preliminar'): Exposicao | null {
  const conf = t.faixa
  const sug = modo === 'preliminar' ? t.faixa_preliminar : null
  const base = s ?? SIM_INICIAL
  const v = (f: Faixa) => maximoPct(f, base)
  const usa = sug && (!conf || v(sug) > v(conf)) ? sug : conf
  if (!usa) return null
  const pct = v(usa)
  return { pct, reais: s ? reaisDe(pct, s) : null, origem: usa === conf ? 'confirmado' : 'sugerido', faixa: usa }
}

function chave(t: Tema, d: Diagnostico | undefined, s: Simulacao | null, modo: Modo): (number | string)[] {
  const degraus = SITUACOES.filter((x) => t.contagem[x]).map((x) => DEGRAU[x])
  const degrau = degraus.length ? Math.min(...degraus) : 5
  const data = t.prazo_mais_urgente?.data ?? '9999-12-31'
  const e = exposicaoTema(t, s, modo)
  // R$ por infração; empate: confirmado antes de sugerido; depois mais obrigações vencidas (cada uma é uma infração possível, o R$ nunca soma); depois o prazo.
  return [d === 'sim' ? 1 : 0, e ? -e.pct : 1, e?.origem === 'sugerido' ? 1 : 0, -t.contagem.vencida, degrau, degrau < 3 ? data : '', -t.n]
}

export function ordenarTemas(temas: Tema[], diag: Diagnosticos = {}, sim: Simulacao | null = SIM_INICIAL, modo: Modo = 'preliminar'): Tema[] {
  return [...temas].sort((a, b) => {
    const ka = chave(a, diag[a.id], sim, modo)
    const kb = chave(b, diag[b.id], sim, modo)
    for (let i = 0; i < ka.length; i++) if (ka[i] !== kb[i]) return ka[i] < kb[i] ? -1 : 1
    return 0
  })
}

/** Situação do prazo do tema em palavras ("prazo vencido há 293 dias"). */
export function situacaoPrazo(t: Tema): string {
  const u = t.prazo_mais_urgente
  if (u && t.contagem.vencida && u.dias != null) return `prazo vencido há ${Math.abs(u.dias)} dias`
  if (u && t.contagem['90dias'] && u.dias != null) return `vence em ${u.dias} dias`
  if (t.contagem.recorrente) return 'obrigação recorrente'
  return 'sem data no texto'
}

/** As 3 decisões da semana: os 3 primeiros temas da ordem que ainda não estão atendidos. */
export function decisoesDaSemana(temas: Tema[], diag: Diagnosticos, sim: Simulacao | null, modo: Modo): Tema[] {
  return ordenarTemas(temas, diag, sim, modo).filter((t) => diag[t.id] !== 'sim').slice(0, 3)
}

/** "3 obrigações vencidas": cada uma é uma infração possível; o R$ nunca é somado. */
export const textoVencidas = (n: number) => `${n} ${n === 1 ? 'obrigação vencida' : 'obrigações vencidas'}`

export interface Manchete {
  temasVencidos: number
  obrigacoesVencidas: number
  maximo: Exposicao | null
  /** Temas vencidos cuja exposição vem só de sugestão (cenário preliminar). */
  sugeridos: number
}

/** Manchete: quantos temas com prazo vencido e a MAIOR exposição por infração entre eles (nunca soma). */
export function manchete(temas: Tema[], diag: Diagnosticos, sim: Simulacao | null, modo: Modo): Manchete {
  const vencidos = temas.filter((t) => t.contagem.vencida && diag[t.id] !== 'sim')
  const exps = vencidos.map((t) => exposicaoTema(t, sim, modo)).filter((e): e is Exposicao => e != null)
  const maximo = exps.length ? exps.reduce((a, b) => (b.pct > a.pct ? b : a)) : null
  return { temasVencidos: vencidos.length, obrigacoesVencidas: vencidos.reduce((n, t) => n + t.contagem.vencida, 0), maximo, sugeridos: exps.filter((e) => e.origem === 'sugerido').length }
}

/** Por que o tema está nesta posição, nas palavras da regra de ordem. */
export function motivoPosicao(t: Tema, d: Diagnostico | undefined, sim: Simulacao | null, modo: Modo): string[] {
  const out: string[] = []
  if (d === 'sim') out.push('Você marcou como já atendido')
  const e = exposicaoTema(t, sim, modo)
  out.push(e ? `Até ${e.reais != null ? brl(e.reais) : pct(e.pct) + ' da receita'} por infração` : 'Exposição a enquadrar')
  out.push(situacaoPrazo(t).replace(/^./, (c) => c.toUpperCase()))
  return out
}

/** Lacuna informada no diagnóstico, em obrigações. */
export function lacuna(temas: Tema[], diag: Diagnosticos) {
  const soma = (d?: Diagnostico) => temas.filter((t) => diag[t.id] === d).reduce((n, t) => n + t.n, 0)
  return {
    nao: soma('nao'),
    parcial: soma('parcial'),
    atendido: soma('sim'),
    semResposta: temas.filter((t) => !diag[t.id]).length,
  }
}

/**
 * Frase-resumo do diagnóstico gerado no navegador: o tema em aberto mais exposto (por infração,
 * nunca soma), a lacuna informada (em obrigações) e quantos temas o enquadramento confirmado libera.
 */
export function resumoDiagnostico(temas: Tema[], diag: Diagnosticos, sim: Simulacao | null, modo: Modo): string {
  const abertos = ordenarTemas(temas, diag, sim, modo).filter((t) => diag[t.id] !== 'sim')
  const topo = abertos.find((t) => exposicaoTema(t, sim, modo))
  const partes: string[] = []
  if (topo) {
    const e = exposicaoTema(topo, sim, modo)!
    const v = e.reais != null ? brl(e.reais) : `${pct(e.pct)} da receita`
    const venc = topo.contagem.vencida ? ` e ${textoVencidas(topo.contagem.vencida)}` : ''
    partes.push(`Neste porte, o tema mais exposto é ${topo.nome}, com até ${v} por infração${venc}${e.origem === 'sugerido' ? ' (enquadramento sugerido, a confirmar)' : ''}`)
  } else partes.push('Neste porte, nenhum tema em aberto tem exposição calculada')
  const g = lacuna(temas, diag)
  if (g.semResposta < temas.length) partes.push(`a lacuna informada é de ${g.nao} obrigações em temas não atendidos e ${g.parcial} em temas parciais`)
  const n = plano.decisoes.confirmar.temas_sem_calculo_confirmado
  partes.push(`confirmar enquadramentos libera o cálculo de ${n} ${n === 1 ? 'tema' : 'temas'}`)
  return partes.join('; ') + '.'
}

export const dataBR = (iso: string) => iso.split('-').reverse().join('/')

/** Número da escala: abaixo de R$ 10 mi, duas casas fixas ("2,50"); de R$ 10 mi para cima, até uma casa ("48,7", "50"). */
const numEscala = (valor: number, n: number) =>
  n.toLocaleString('pt-BR', valor < 1e7 ? { minimumFractionDigits: 2, maximumFractionDigits: 2 } : { maximumFractionDigits: 1 })

export function brl(valor: number): string {
  // Singular abaixo de 2: "R$ 1 bilhão", "R$ 1,50 milhão".
  const escala = (n: number, um: string, varios: string) => `R$ ${numEscala(valor, n)} ${n < 2 ? um : varios}`
  if (valor >= 1e9) return escala(valor / 1e9, 'bilhão', 'bilhões')
  if (valor >= 1e6) return escala(valor / 1e6, 'milhão', 'milhões')
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export const pct = (v: number) => `${v.toLocaleString('pt-BR', { maximumFractionDigits: 3 })}%`

// Simulador por porte: a mesma conta de athenix/impacto.py (multa e teto_legal), sem agravantes,
// refeita no navegador com a base informada. Nada é enviado. O teste compara com os casos de
// conferência que o exportador calcula com o motor Python (plano.simulador.conferencia).
export interface Simulacao { base: number; faturamento: number | null }
export const SIM_INICIAL: Simulacao = { base: plano.perfil.base_reais, faturamento: null }
const REDUCAO_CENARIO = Object.fromEntries(
  plano.reducao.medidas.filter((m) => m.cenario && m.percentual != null).map((m) => [m.cenario, m.percentual]),
) as Partial<Record<Cenario, number>>

/** Teto legal em % da base: % do faturamento convertido quando o faturamento é informado (D6). */
export function tetoLegalPct(f: Faixa, s: Simulacao): number {
  if (f.teto_legal_lei_pct == null) return Infinity
  return s.faturamento != null && s.base ? (f.teto_legal_lei_pct * s.faturamento) / s.base : f.teto_legal_lei_pct
}

/** Máximo por infração em % da base: teto do grupo limitado pelo teto legal. */
export const maximoPct = (f: Faixa, s: Simulacao) => Math.min(f.teto_grupo_pct, tetoLegalPct(f, s))

/** Com atenuante (só se o motor calculou este cenário): teto do grupo menos o percentual do art. 24. */
export function comAtenuantePct(f: Faixa, s: Simulacao, c: Cenario): number | null {
  const r = REDUCAO_CENARIO[c]
  if (f.com_atenuante_pct[c] == null || r == null) return null
  return Math.min(f.teto_grupo_pct * (1 - r / 100), tetoLegalPct(f, s))
}

export const reaisDe = (pctBase: number, s: Simulacao) => (pctBase / 100) * s.base

/** Valor em reais digitado: "7.500.000.000", "7500000000" ou "7.500.000.000,00". Inválido: null. */
export function lerReais(texto: string): number | null {
  let t = texto.replace(/R\$|\s/g, '')
  if (!t) return null
  t = t.includes(',') ? t.replaceAll('.', '').replace(',', '.') : t.replaceAll('.', '')
  if (!/^\d+(\.\d+)?$/.test(t)) return null
  const v = Number(t)
  return Number.isFinite(v) && v > 0 && v <= 1e13 ? v : null
}

/** Valor por infração: "até R$ X por infração", nunca "R$ 0 a R$ X". Sem base: em % da base. */
export function textoFaixa(f: Faixa, s: Simulacao | null = SIM_INICIAL): string {
  const teto = s ? brl(reaisDe(maximoPct(f, s), s)) : `${pct(maximoPct(f, SIM_INICIAL))} da base`
  return `até ${teto} por infração`
}
export const NOTA_ADVERTENCIA = 'pode ser só advertência'

/** "R$ 2,50 mi", "R$ 50 mi", "R$ 48,7 mi", "R$ 1 bi": para a manchete. */
export function brlCurto(v: number): string {
  const f = (n: number, u: string) => `R$ ${numEscala(v, n)} ${u}`
  return v >= 1e9 ? f(v / 1e9, 'bi') : v >= 1e6 ? f(v / 1e6, 'mi') : brl(v)
}

const NOMES_DIAG: Record<Diagnostico, string> = { sim: 'Já temos', parcial: 'Parcial', nao: 'Não temos' }
export const nomeDiag = (d?: Diagnostico) => (d ? NOMES_DIAG[d] : 'Não informado')

/** Célula de CSV: aspas, e fórmula neutralizada (=, +, -, @ no início viram texto). */
export function celula(v: unknown): string {
  let s = v == null ? '' : String(v)
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`
  return `"${s.replaceAll('"', '""')}"`
}

/** Colunas a mais no CSV (injetadas por quem as conhece: respostas e provas ficam fora deste módulo). */
export interface ExtrasCsv { colunas: string[]; linha: (tema: Tema, o: Obrigacao) => unknown[] }

export function csvPlano(diag: Diagnosticos, s: Simulacao | null = SIM_INICIAL, extras?: ExtrasCsv): string {
  // A planilha só traz o que o texto da obrigação confirma: a ordem usa o modo 'confirmados'.
  const temas = ordenarTemas(plano.temas, diag, s, 'confirmados')
  const linhas: unknown[][] = [
    ['Plano de ação — ' + plano.norma.titulo + ' — ' + plano.perfil.rotulo + (s ? ' — receita operacional líquida considerada: ' + brl(s.base) + ' (premissa informada ou ilustrativa)' : '')],
    ['ESTIMATIVA ILUSTRATIVA. ' + plano.perfil.aviso + ' ' + plano.aviso + ' Iniciativa em validação.'],
    ['Interpretações da IA aguardam revisão humana e não entram no cálculo. Diagnóstico informado só nesta planilha; nada foi enviado.'],
    [],
    ['Ordem do tema', 'Tema', 'Diagnóstico', 'Obrigação', 'Dispositivo', 'Situação do prazo', 'Prazo', 'Enquadramento identificado (REN 846)', 'Grupo', 'Exposição máxima por infração', 'Interpretação da IA (não entra no cálculo)', 'Evidência sugerida', 'Trecho literal da norma', 'Fonte', ...(extras?.colunas ?? [])],
  ]
  temas.forEach((t, n) => {
    for (const id of t.obrigacoes) {
      const o = obrigacao(id)
      linhas.push([
        n + 1,
        t.nome,
        nomeDiag(diag[t.id]),
        o.titulo_completo,
        o.dispositivo,
        plano.nomes_situacao[o.situacao],
        o.prazo.data ? dataBR(o.prazo.data) + (o.prazo.provisorio ? ' (provisório)' : '') : o.prazo.texto,
        o.enquadramento.map((e) => e.dispositivo).join('; '),
        o.grupo ?? 'a confirmar',
        o.faixa ? `${textoFaixa(o.faixa, s)} (${NOTA_ADVERTENCIA})` : o.motivo_sem_calculo ?? 'Enquadramento a confirmar',
        o.ia ? `${o.ia.dispositivo} (Grupo ${o.ia.grupo})${o.ia.duvida ? ' · depende da dúvida ' + o.ia.duvida : ''}` : '',
        o.evidencias.map((e) => plano.evidencias[e.id]).join('; '),
        o.trecho,
        plano.norma.url,
        ...(extras ? extras.linha(t, o) : []),
      ])
    }
  })
  return '﻿' + linhas.map((l) => l.map(celula).join(';')).join('\r\n') + '\r\n'
}
