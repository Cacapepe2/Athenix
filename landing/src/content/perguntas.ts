// "Perguntas para levar ao jurídico": lista gerada do que o próprio Athenix marca como incerto no plano:
// enquadramentos sugeridos pela IA (os das 5 primeiras obrigações antes), enquadramentos a confirmar por tema,
// as duas redações do art. 11, XXIII, dependências externas que podem servir de excludente e prazos que dependem
// de instruções da ANEEL. Cada pergunta é curta e traz o dispositivo e a citação. Nada é inventado: sem o sinal
// de incerteza nos dados, não há pergunta. Lógica pura, testada em perguntas.test.ts.
import { top5 } from './executivo.ts'
import type { Modo, NormaId, Obrigacao, PlanoDados, Simulacao } from './plano.ts'

export const ABERTURA_PERGUNTAS = 'O Athenix prepara a conversa com o jurídico; não a substitui.'

export type Origem = 'enquadramento_topo' | 'enquadramento_tema' | 'sucessao_no_tempo' | 'excludente' | 'instrucao_aneel'
export interface Pergunta { origem: Origem; pergunta: string; dispositivo: string; citacao: string; fontes: { sha256: string; trecho: string; rotulo: string }[] }

const curta = (t: string, n = 240) => (t.length <= n ? t : `${t.slice(0, n).replace(/\s+\S*$/, '')}…`)
const cit = (t: string | null | undefined) => (t ? `“${curta(t.trim())}”` : '—')

export function perguntasParaOJuridico(p: PlanoDados, normaId: NormaId, s: Simulacao | null = null, modo: Modo = 'preliminar', hoje?: string): Pergunta[] {
  const por = new Map(p.obrigacoes.map((o) => [o.id, o]))
  const saida: Pergunta[] = []

  // 1. Enquadramentos sugeridos pela IA nas 5 obrigações do topo (primeiro).
  const topo = new Set<string>()
  for (const l of top5(normaId, s, modo, 5, hoje)) {
    const o = por.get(l.id)
    if (!o?.ia || o.faixa) continue
    topo.add(o.id)
    saida.push({ origem: 'enquadramento_topo', pergunta: `A IA sugere enquadrar esta obrigação no ${o.ia.dispositivo} da REN 846 (Grupo ${o.ia.grupo}). Vocês concordam?${o.ia.duvida ? ` Dúvida registrada: ${o.ia.duvida}.` : ''}`, dispositivo: o.dispositivo ?? 'dispositivo a confirmar', citacao: cit(o.trecho), fontes: [{ sha256: p.norma.sha256, trecho: o.trecho ?? '', rotulo: o.dispositivo ?? '' }] })
  }

  // 2. Enquadramentos a confirmar: UMA pergunta, com o total e a quantidade por tema.
  const porTema = p.temas.map((t) => ({ t, restantes: t.obrigacoes.map((id) => por.get(id)).filter((o): o is Obrigacao => !!o && !o.faixa && !topo.has(o.id)) })).filter((x) => x.restantes.length)
  const total = porTema.reduce((n, x) => n + x.restantes.length, 0)
  if (total) {
    const maior = [...porTema].sort((m, n) => n.restantes.length - m.restantes.length)[0]
    const ref = maior.restantes.find((o) => o.ia) ?? maior.restantes[0]
    const sugeridas = porTema.reduce((n, x) => n + x.restantes.filter((o) => o.ia).length, 0)
    saida.push({
      origem: 'enquadramento_tema',
      pergunta: `Enquadramento a confirmar em ${total} ${total === 1 ? 'obrigação' : 'obrigações'}${sugeridas ? ` (${sugeridas} com sugestão da IA)` : ''}: ${porTema.map((x) => `${x.t.nome} (${x.restantes.length})`).join('; ')}. Qual infração da REN 846 se aplica a cada grupo?`,
      dispositivo: ref.dispositivo ?? 'dispositivo a confirmar', citacao: `exemplo, tema “${maior.t.nome}”: ${cit(ref.trecho)}`, fontes: [{ sha256: p.norma.sha256, trecho: ref.trecho ?? '', rotulo: ref.dispositivo ?? '' }],
    })
  }

  // 3. Duas redações do mesmo dispositivo (hoje o art. 11, XXIII da REN 846).
  for (const sc of p.sucessao_no_tempo ?? []) {
    saida.push({
      origem: 'sucessao_no_tempo',
      pergunta: `${sc.dispositivo}: há ${sc.redacoes.length} redações em datas diferentes (${sc.redacoes.map((r) => r.ato).join(' e ')}). Qual vale para cada fato? ${sc.texto_da_duvida}`,
      dispositivo: sc.dispositivo, citacao: sc.redacoes.map((r) => `${r.ato}: ${cit(r.trecho)}`).join(' | '), fontes: sc.redacoes.map((r) => ({ sha256: r.fonte.sha256, trecho: r.trecho, rotulo: r.ato })),
    })
  }

  // 4. Dependências externas que podem servir de excludente e 5. prazos que dependem de ato da ANEEL: uma pergunta por tipo de dependência.
  const grupos = new Map<string, { nome: string; achados: { dispositivo: string; trecho: string; trechoFonte: string; tema: string }[] }>()
  for (const t of p.temas) {
    for (const d of t.dependencias_no_texto) {
      const g = grupos.get(d.id) ?? { nome: p.analise.dependencias[d.id]?.nome ?? d.id, achados: [] }
      g.achados.push({ dispositivo: por.get(d.obrigacao)?.dispositivo ?? 'dispositivo a confirmar', trecho: d.trecho_literal, trechoFonte: por.get(d.obrigacao)?.trecho ?? d.trecho_literal, tema: t.nome })
      grupos.set(d.id, g)
    }
  }
  for (const [id, g] of grupos) {
    const n = g.achados.length
    const primeiro = g.achados[0]
    const resto = n > 1 ? ` e mais ${n - 1} ${n - 1 === 1 ? 'dispositivo' : 'dispositivos'}: ${g.achados.slice(1, 4).map((x) => x.dispositivo).join('; ')}${n > 4 ? '…' : ''}` : ''
    if (id === 'ato_da_aneel') {
      saida.push({ origem: 'instrucao_aneel', pergunta: `O prazo depende de instruções da ANEEL em ${n} ${n === 1 ? 'dispositivo' : 'dispositivos'} (${g.nome}). Conta da publicação do ato? Cabe pedir esclarecimento ou prorrogação?`, dispositivo: `${primeiro.dispositivo}${resto}`, citacao: cit(primeiro.trecho), fontes: [{ sha256: p.norma.sha256, trecho: primeiro.trechoFonte, rotulo: primeiro.dispositivo }] })
    } else {
      saida.push({ origem: 'excludente', pergunta: `“${g.nome}” pode servir de excludente em ${n} ${n === 1 ? 'dispositivo' : 'dispositivos'}? O que precisa estar documentado?`, dispositivo: `${primeiro.dispositivo}${resto}`, citacao: cit(primeiro.trecho), fontes: [{ sha256: p.norma.sha256, trecho: primeiro.trechoFonte, rotulo: primeiro.dispositivo }] })
    }
  }
  return saida
}
