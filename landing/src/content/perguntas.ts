// "Perguntas para levar ao jurídico": lista gerada do que o próprio Athenix marca como incerto no plano:
// enquadramentos sugeridos pela IA (os das 5 primeiras obrigações antes), enquadramentos a confirmar por tema,
// as duas redações do art. 11, XXIII, dependências externas que podem servir de excludente e prazos que dependem
// de instruções da ANEEL. Cada pergunta é curta e traz o dispositivo e a citação. Nada é inventado: sem o sinal
// de incerteza nos dados, não há pergunta. Lógica pura, testada em perguntas.test.ts.
import { top5 } from './executivo.ts'
import type { Modo, NormaId, Obrigacao, PlanoDados, Simulacao } from './plano.ts'

export const ABERTURA_PERGUNTAS = 'O Athenix prepara a conversa com o jurídico; não a substitui.'

export type Origem = 'enquadramento_topo' | 'enquadramento_tema' | 'sucessao_no_tempo' | 'excludente' | 'instrucao_aneel'
export interface Pergunta { origem: Origem; pergunta: string; dispositivo: string; citacao: string }

const curta = (t: string, n = 240) => (t.length <= n ? t : `${t.slice(0, n).replace(/\s+\S*$/, '')}…`)
const cit = (t: string | null | undefined) => (t ? `“${curta(t.trim())}”` : '—')

export function perguntasParaOJuridico(p: PlanoDados, normaId: NormaId, s: Simulacao | null = null, modo: Modo = 'preliminar'): Pergunta[] {
  const por = new Map(p.obrigacoes.map((o) => [o.id, o]))
  const saida: Pergunta[] = []

  // 1. Enquadramentos sugeridos pela IA nas 5 obrigações do topo (primeiro).
  const topo = new Set<string>()
  for (const l of top5(normaId, s, modo)) {
    const o = por.get(l.id)
    if (!o?.ia || o.faixa) continue
    topo.add(o.id)
    saida.push({ origem: 'enquadramento_topo', pergunta: `A IA sugere enquadrar esta obrigação no ${o.ia.dispositivo} da REN 846 (Grupo ${o.ia.grupo}). Vocês concordam?${o.ia.duvida ? ` Dúvida registrada: ${o.ia.duvida}.` : ''}`, dispositivo: o.dispositivo ?? 'dispositivo a confirmar', citacao: cit(o.trecho) })
  }

  // 2. Enquadramentos a confirmar, agrupados por tema (com a quantidade).
  for (const t of p.temas) {
    const restantes = t.obrigacoes.map((id) => por.get(id)).filter((o): o is Obrigacao => !!o && !o.faixa && !topo.has(o.id))
    if (!restantes.length) continue
    const sugeridas = restantes.filter((o) => o.ia).length
    const ref = restantes.find((o) => o.ia) ?? restantes[0]
    saida.push({
      origem: 'enquadramento_tema',
      pergunta: `Tema “${t.nome}”: ${restantes.length} ${restantes.length === 1 ? 'obrigação com enquadramento a confirmar' : 'obrigações com enquadramento a confirmar'}${sugeridas ? `, ${sugeridas} com sugestão da IA${t.ia ? ` (${t.ia.dispositivo})` : ''}` : ''}. Qual infração da REN 846 se aplica?`,
      dispositivo: ref.dispositivo ?? 'dispositivo a confirmar', citacao: cit(ref.trecho),
    })
  }

  // 3. Duas redações do mesmo dispositivo (hoje o art. 11, XXIII da REN 846).
  for (const sc of p.sucessao_no_tempo ?? []) {
    saida.push({
      origem: 'sucessao_no_tempo',
      pergunta: `${sc.dispositivo}: há ${sc.redacoes.length} redações em datas diferentes (${sc.redacoes.map((r) => r.ato).join(' e ')}). Qual vale para cada fato? ${sc.texto_da_duvida}`,
      dispositivo: sc.dispositivo, citacao: sc.redacoes.map((r) => `${r.ato}: ${cit(r.trecho)}`).join(' | '),
    })
  }

  // 4. Dependências externas que podem servir de excludente (por tema, só as achadas no texto) e 5. prazos que dependem de ato da ANEEL.
  for (const t of p.temas) {
    for (const d of t.dependencias_no_texto) {
      const o = por.get(d.obrigacao)
      const nome = p.analise.dependencias[d.id]?.nome ?? d.id
      if (d.id === 'ato_da_aneel') {
        saida.push({ origem: 'instrucao_aneel', pergunta: `O prazo depende de instruções da ANEEL (${nome}). Conta da publicação do ato? Cabe pedir esclarecimento ou prorrogação?`, dispositivo: o?.dispositivo ?? 'dispositivo a confirmar', citacao: cit(d.trecho_literal) })
      } else {
        saida.push({ origem: 'excludente', pergunta: `“${nome}” pode servir de excludente neste tema? O que precisa estar documentado?`, dispositivo: o?.dispositivo ?? 'dispositivo a confirmar', citacao: cit(d.trecho_literal) })
      }
    }
  }
  return saida
}
