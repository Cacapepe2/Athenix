// Uma referência de data por renderização: o plano vem do JSON com os dias da data de geração (17/11/2026);
// aqui tudo que depende de "hoje" (situação, dias, texto do prazo, contagens por tema e totais) é recalculado
// a partir da data de VENCIMENTO e de UMA data de referência recebida. Nada de texto congelado. Lógica pura,
// testada em referencia.test.ts (com datas injetadas).
import { atualizar } from './datas.ts'
import type { Obrigacao, PlanoDados, Situacao, Tema } from './plano.ts'

const SITUACOES: Situacao[] = ['vencida', '90dias', 'depois', 'recorrente', 'evento', 'sem_prazo']
const br = (iso: string) => iso.split('-').reverse().join('/')

/** "Vencido desde 28/01/2026 (297 dias)" / "Vence em 04/11/2027 (348 dias)"; sem data, o texto do JSON. */
export function textoDoPrazo(o: Obrigacao): string {
  const d = o.prazo.data
  if (!d || o.prazo.dias == null) return o.prazo.texto
  return o.situacao === 'vencida' ? `Vencido desde ${br(d)} (${Math.abs(o.prazo.dias)} dias)` : `Vence em ${br(d)} (${o.prazo.dias} dias)`
}

export function obrigacaoEm(o: Obrigacao, hoje: string): Obrigacao {
  const a = atualizar(o, hoje)
  return a === o ? o : { ...a, prazo: { ...a.prazo, texto: textoDoPrazo(a) } }
}

function temaEm(t: Tema, por: Map<string, Obrigacao>): Tema {
  const obs = t.obrigacoes.map((id) => por.get(id)!).filter(Boolean)
  const contagem = Object.fromEntries(SITUACOES.map((s) => [s, obs.filter((o) => o.situacao === s).length])) as Record<Situacao, number>
  const comData = obs.filter((o) => o.prazo.data)
  const u = comData.length ? comData.reduce((a, b) => (b.prazo.data! < a.prazo.data! ? b : a)) : null
  return { ...t, contagem, prazo_mais_urgente: u ? { obrigacao: u.id, data: u.prazo.data, texto: u.prazo.texto, dias: u.prazo.dias, situacao: u.situacao } : null }
}

/** O plano inteiro para a data `hoje` (AAAA-MM-DD): obrigações, temas, totais e linha do tempo coerentes entre si. */
export function planoEm(p: PlanoDados, hoje: string): PlanoDados {
  const obrigacoes = p.obrigacoes.map((o) => obrigacaoEm(o, hoje))
  const por = new Map(obrigacoes.map((o) => [o.id, o]))
  const porSituacao = Object.fromEntries(SITUACOES.map((s) => [s, obrigacoes.filter((o) => o.situacao === s).length])) as Record<Situacao, number>
  const linha = Object.fromEntries(SITUACOES.map((s) => [s, obrigacoes.filter((o) => o.situacao === s).map((o) => o.id)])) as Record<Situacao, string[]>
  return {
    ...p, obrigacoes,
    temas: p.temas.map((t) => temaEm(t, por)),
    resumo: { ...p.resumo, por_situacao: porSituacao },
    linha_do_tempo: { ...p.linha_do_tempo, ...linha },
  }
}
