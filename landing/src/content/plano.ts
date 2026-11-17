// Plano de ação da RN ANEEL 1.137/2025 para uma distribuidora ilustrativa. Dados gerados por
// scripts/exportar_plano_demo.py a partir do produto (athenix/plano.py): nenhum número é digitado aqui.
// Interpretações da IA vêm de um cache revisável, aparecem marcadas e nunca entram no cálculo.
import dados from './plano-rn1137.json' with { type: 'json' }

export type Situacao = 'vencida' | '90dias' | 'depois' | 'recorrente' | 'evento' | 'sem_prazo'
export type Diagnostico = 'sim' | 'parcial' | 'nao'
export type Diagnosticos = Partial<Record<string, Diagnostico>>

export interface Faixa {
  grupos: string[]
  teto_grupo_pct: number
  maximo_pct: { com_teto: number; sem_teto: number }
  teto_legal_pct: number | null
  teto_legal_subestimado: boolean | null
  maximo_reais?: { com_teto: number; sem_teto: number }
}

export interface Obrigacao {
  id: string
  titulo: string
  titulo_origem: 'regra' | 'ia'
  tema: string
  motivo_tema: string
  unidade: string | null
  dispositivo: string | null
  trecho: string | null
  situacao: Situacao
  prazo: { data: string | null; texto: string; dias: number | null; provisorio: boolean }
  calculo: 'fila' | 'verificar' | 'sem_multa'
  posicao_fila: number | null
  enquadramento: { dispositivo: string; grupo: string }[]
  ia: { dispositivo: string; grupo: string; justificativa: string; duvida: string | null } | null
  grupo: string | null
  faixa: Faixa | null
  premissas: string[]
  motivo_sem_calculo: string | null
  evidencias: { id: string; trecho: string }[]
}

export interface Tema {
  id: string
  nome: string
  fontes: { rotulo: string; titulo: string; unidade: string }[]
  n: number
  contagem: Record<Situacao, number>
  prazo_mais_urgente: { obrigacao: string; data: string | null; texto: string; situacao: Situacao } | null
  na_fila: number
  a_confirmar: number
  grupos: string[]
  grupo_mais_grave: string | null
  infracoes: string[]
  faixa: Faixa | null
  ia: { dispositivo: string; n: number; de: number } | null
  evidencias: { id: string; n: number; exemplo: { obrigacao: string; trecho: string } }[]
  principais: string[]
  obrigacoes: string[]
}

export const plano = dados as unknown as {
  gerado_por: string
  commit_origem: string
  gerado_em: string
  aviso: string
  norma: { titulo: string; url: string; sha256: string; vigencia: string }
  perfil: { rotulo: string; aviso: string; base_reais: number; origem_base: string; data_referencia: string }
  ia: { aviso: string; modelo: string; reasoning: string; criterio_titulos: string; criterio_enquadramentos: string } | null
  resumo: {
    identificadas: number
    aplicaveis: number
    fora_do_perfil: number
    por_situacao: Record<Situacao, number>
    na_fila: number
    a_confirmar: number
    sem_multa: number
    grupo_mais_grave: string | null
    temas: number
  }
  decisoes: { titulo: string; itens: string[]; obrigacoes: string[]; temas: string[]; motivo: string }[]
  temas: Tema[]
  ordem_inicial: string[]
  obrigacoes: Obrigacao[]
  infracoes: Record<string, { grupo: string; trecho: string }>
  linha_do_tempo: Record<Situacao, string[]>
  nomes_situacao: Record<Situacao, string>
  regra_ordem: string
  evidencias: Record<string, string>
}

export const obrigacaoPorId = new Map(plano.obrigacoes.map((o) => [o.id, o]))
export const obrigacao = (id: string) => obrigacaoPorId.get(id)!

export const SITUACOES: Situacao[] = ['vencida', '90dias', 'depois', 'recorrente', 'evento', 'sem_prazo']
const GRUPOS = ['I', 'II', 'III', 'IV', 'V']
// Mesma regra de athenix/plano.py (ordenar_temas); o teste compara com plano.ordem_inicial.
const DEGRAU: Record<Situacao, number> = { vencida: 0, '90dias': 1, depois: 2, recorrente: 3, evento: 4, sem_prazo: 4 }
const LACUNA: Partial<Record<Diagnostico, number>> = { nao: 0, parcial: 1 }

function chave(t: Tema, d?: Diagnostico): (number | string)[] {
  const degraus = SITUACOES.filter((s) => t.contagem[s]).map((s) => DEGRAU[s])
  const degrau = degraus.length ? Math.min(...degraus) : 5
  const data = t.prazo_mais_urgente?.data ?? '9999-12-31'
  const grav = t.grupo_mais_grave ? GRUPOS.indexOf(t.grupo_mais_grave) : -1
  return [d === 'sim' ? 1 : 0, degrau, degrau < 3 ? data : '', -grav, LACUNA[d as Diagnostico] ?? 2, -t.n]
}

export function ordenarTemas(temas: Tema[], diag: Diagnosticos = {}): Tema[] {
  return [...temas].sort((a, b) => {
    const ka = chave(a, diag[a.id])
    const kb = chave(b, diag[b.id])
    for (let i = 0; i < ka.length; i++) if (ka[i] !== kb[i]) return ka[i] < kb[i] ? -1 : 1
    return 0
  })
}

/** Por que o tema está nesta posição, nas palavras da regra de ordem. */
export function motivoPosicao(t: Tema, d?: Diagnostico): string[] {
  const out: string[] = []
  if (d === 'sim') out.push('Você marcou como já atendido')
  const u = t.prazo_mais_urgente
  if (t.contagem.vencida && u) out.push(`Prazo vencido desde ${dataBR(u.data!)}`)
  else if (t.contagem['90dias'] && u) out.push(`Vence em ${dataBR(u.data!)}`)
  else if (t.contagem.recorrente) out.push('Obrigação recorrente')
  else out.push('Sem data no texto')
  out.push(t.grupo_mais_grave ? `Grupo ${t.grupo_mais_grave} de infração` : 'Enquadramento a confirmar')
  if (d === 'nao') out.push('Lacuna: não temos')
  if (d === 'parcial') out.push('Lacuna: parcial')
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

export const dataBR = (iso: string) => iso.split('-').reverse().join('/')

export function brl(valor: number): string {
  if (valor >= 1e9) return `R$ ${(valor / 1e9).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} bilhões`
  if (valor >= 1e6) return `R$ ${(valor / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} milhões`
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export const pct = (v: number) => `${v.toLocaleString('pt-BR', { maximumFractionDigits: 3 })}%`

/** Faixa por infração: "advertência até R$ X", nunca "R$ 0 a R$ X". */
export function textoFaixa(f: Faixa): string {
  const teto = f.maximo_reais ? brl(f.maximo_reais.com_teto) : `${pct(f.maximo_pct.com_teto)} da base`
  return `De advertência (sem multa) até ${teto} por infração`
}

const NOMES_DIAG: Record<Diagnostico, string> = { sim: 'Já temos', parcial: 'Parcial', nao: 'Não temos' }
export const nomeDiag = (d?: Diagnostico) => (d ? NOMES_DIAG[d] : 'Não informado')

/** Célula de CSV: aspas, e fórmula neutralizada (=, +, -, @ no início viram texto). */
export function celula(v: unknown): string {
  let s = v == null ? '' : String(v)
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`
  return `"${s.replaceAll('"', '""')}"`
}

export function csvPlano(diag: Diagnosticos): string {
  const temas = ordenarTemas(plano.temas, diag)
  const linhas: unknown[][] = [
    ['Plano de ação — ' + plano.norma.titulo + ' — ' + plano.perfil.rotulo],
    ['ESTIMATIVA ILUSTRATIVA. ' + plano.perfil.aviso + ' ' + plano.aviso + ' Iniciativa em validação.'],
    ['Interpretações da IA aguardam revisão humana e não entram no cálculo. Diagnóstico informado só nesta planilha; nada foi enviado.'],
    [],
    ['Ordem do tema', 'Tema', 'Diagnóstico', 'Obrigação', 'Dispositivo', 'Situação do prazo', 'Prazo', 'Enquadramento identificado (REN 846)', 'Grupo', 'Exposição máxima por infração', 'Interpretação da IA (não entra no cálculo)', 'Evidência sugerida', 'Trecho literal da norma', 'Fonte'],
  ]
  temas.forEach((t, n) => {
    for (const id of t.obrigacoes) {
      const o = obrigacao(id)
      linhas.push([
        n + 1,
        t.nome,
        nomeDiag(diag[t.id]),
        o.titulo,
        o.dispositivo,
        plano.nomes_situacao[o.situacao],
        o.prazo.data ? dataBR(o.prazo.data) + (o.prazo.provisorio ? ' (provisório)' : '') : o.prazo.texto,
        o.enquadramento.map((e) => e.dispositivo).join('; '),
        o.grupo ?? 'a confirmar',
        o.faixa ? textoFaixa(o.faixa) : o.motivo_sem_calculo ?? 'Enquadramento a confirmar',
        o.ia ? `${o.ia.dispositivo} (Grupo ${o.ia.grupo})${o.ia.duvida ? ' · depende da dúvida ' + o.ia.duvida : ''}` : '',
        o.evidencias.map((e) => plano.evidencias[e.id]).join('; '),
        o.trecho,
        plano.norma.url,
      ])
    }
  })
  return '﻿' + linhas.map((l) => l.map(celula).join(';')).join('\r\n') + '\r\n'
}
