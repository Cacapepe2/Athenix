// "Baixar meu relatório": o relatório de trabalho (impressão/PDF) e as colunas novas do CSV. Tudo vem do plano
// (mesmos números da executiva e do plano completo) e do que a empresa escreveu e marcou no navegador.
// Lógica pura, testada em relatorio.test.ts. Nada sai do navegador.
import { prazos, queda, textoPrazoDoTema, tituloCurto, valorGeral } from './executivo.ts'
import { atualizar } from './datas.ts'
import { planoEm } from './referencia.ts'
import { provasDoTema, recomendacoesDoTema } from './recomendacoes.ts'
import { normaDaUrl, textoVencidasComDetalhe, decisoesDaSemana, nomeDiag, brlCurto, comAtenuantePct, dataBR, exposicaoTema, ordenarTemas, pct, plano as planoDaPagina, HOJE, reaisDe, SIM_INICIAL, type Diagnosticos, type ExtrasCsv, type Modo, type Obrigacao, type Simulacao, type Tema } from './plano.ts'
import { fraseProntidao, prontidao } from './prontidao.ts'
import { perguntasParaOJuridico, type Pergunta } from './perguntas.ts'
import type { Respostas } from './respostas.ts'

export const AVISO_RELATORIO = 'Análise regulatória preliminar · não constitui parecer jurídico'

const obrigacoesDoTema = (t: Tema): Obrigacao[] => t.obrigacoes.map((id) => planoDaPagina.obrigacoes.find((o) => o.id === id)!).filter(Boolean)

/** Colunas novas do CSV do plano: o que já fazem, situação informada, provas marcadas e área sugerida. */
export function extrasDoCsv(r: Respostas, diag: Diagnosticos = {}): ExtrasCsv {
  return {
    colunas: ['o_que_ja_fazemos', 'situacao', 'provas_marcadas', 'area', 'sujeito'],
    linha: (t, o) => {
      const marcadas = new Set(r.provas[t.id] ?? [])
      const texto = provasDoTema(planoDaPagina, obrigacoesDoTema(t)).filter((p) => marcadas.has(p.id)).map((p) => p.texto).join('; ')
      return [r.jaFazemos[t.id] ?? '', diag[t.id] ? nomeDiag(diag[t.id]) : '', texto, o.area, o.sujeito_implicito ? 'sujeito implícito (a revisar)' : 'distribuidora (no texto)']
    },
  }
}

export interface LinhaTemaRelatorio {
  id: string
  nome: string
  citacao: string
  dispositivo: string
  prazo: string
  exposicao: { teto: string; ii: string | null; i: string | null; preliminar: boolean } | null
  acoes: string[]
  provas: { id: string; texto: string; marcada: boolean }[]
  jaFazemos: string
  situacao: string
}
export interface AreaRelatorio { area: string; n: number; vencidas: number; viaIA: number; frase: string }
export interface Relatorio {
  cabecalho: { norma: string; porte: string; data: string; prazosAte: string; aviso: string }
  numeros: { exposicao: string; porInfracao: string; reducao: string; prazo: { valor: string; legenda: string } }
  decisoes: { nome: string; porque: string }[]
  /** Só existe depois de o usuário marcar alguma prova. */
  prontidao: string | null
  temas: LinhaTemaRelatorio[]
  lacunas: { nome: string; motivo: string }[]
  areas: AreaRelatorio[]
  perguntas: Pergunta[]
}

/** AAAA-MM-DD no fuso do navegador (toISOString usaria UTC e trocaria o dia à noite). */
const diaLocal = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const curta = (t: string, n = 220) => (t.length <= n ? t : `${t.slice(0, n).replace(/\s+\S*$/, '')}…`)

export function montarRelatorio(args: { sim: Simulacao | null; modo: Modo; diag: Diagnosticos; respostas: Respostas; hoje?: Date | string }): Relatorio {
  const { sim, modo, diag, respostas } = args
  // UMA referência de data para o relatório inteiro (a recebida; sem ela, a da página).
  const hojeIso = typeof args.hoje === 'string' ? args.hoje : args.hoje ? diaLocal(args.hoje) : HOJE
  const plano = planoEm(planoDaPagina, hojeIso)
  const base = sim ?? SIM_INICIAL
  const v = valorGeral(plano, sim, modo)
  const q = queda(plano, sim, modo)
  const pz = prazos(plano, hojeIso)
  const dinheiro = (p: number) => (sim ? brlCurto(reaisDe(p, sim)) : `${pct(p)} da receita`)
  const ordenados = ordenarTemas(plano.temas, diag, sim, modo)

  const temas = ordenados.map<LinhaTemaRelatorio>((t) => {
    const rec = recomendacoesDoTema(plano, t, sim, modo)
    const e = exposicaoTema(t, sim, modo)
    const principal = plano.obrigacoes.find((o) => o.id === t.principais[0])
    const marcadas = new Set(respostas.provas[t.id] ?? [])
    const ii = e ? comAtenuantePct(e.faixa, base, 'ate_tn') : null
    const i = e ? comAtenuantePct(e.faixa, base, 'espontanea') : null
    return {
      id: t.id, nome: t.nome,
      citacao: principal?.trecho ? `“${curta(principal.trecho.trim())}”` : principal?.titulo_completo ?? '—',
      dispositivo: principal?.dispositivo ?? 'dispositivo a confirmar',
      prazo: textoPrazoDoTema(plano, t, hojeIso),
      exposicao: e ? { teto: dinheiro(e.pct), ii: ii != null ? dinheiro(ii) : null, i: i != null ? dinheiro(i) : null, preliminar: e.origem === 'sugerido' } : null,
      acoes: rec.acoes,
      provas: rec.provas.map((p) => ({ ...p, marcada: marcadas.has(p.id) })),
      jaFazemos: respostas.jaFazemos[t.id] ?? '',
      situacao: nomeDiag(diag[t.id]),
    }
  })

  const lacunas = temas.flatMap((t) => {
    const d = diag[t.id]
    const faltam = t.provas.filter((p) => !p.marcada).length
    if (d === 'sim' && !faltam) return []
    if (d !== 'parcial' && d !== 'nao') return faltam && Object.values(respostas.provas).some((v) => v.length) ? [{ nome: t.nome, motivo: `${faltam} prova(s) sem marcar` }] : []
    return [{ nome: t.nome, motivo: `${nomeDiag(d)}${faltam ? ` · ${faltam} prova(s) sem marcar` : ''}` }]
  })

  const lista = plano.analise.areas.lista
  const areas = lista.flatMap<AreaRelatorio>((area) => {
    const os = plano.obrigacoes.filter((o) => o.area === area)
    if (!os.length) return []
    const venc = os.map((o) => atualizar(o, hojeIso)).filter((o) => o.situacao === 'vencida').sort((a, b) => (a.prazo.data ?? '').localeCompare(b.prazo.data ?? ''))
    const frase = area === 'A definir' ? `A definir: ${os.length} obrigações sem tipo identificado; a área responsável fica para a empresa decidir` : venc.length ? `${area}: ${os.length} obrigações, ${venc.length} vencidas — comece por ${venc.length > 3 ? 'estas 3' : venc.length === 1 ? 'esta' : `estas ${venc.length}`}: ${venc.slice(0, 3).map((o) => tituloCurto(o)).join('; ')}` : `${area}: ${os.length} obrigações, nenhuma vencida`
    const viaIA = os.filter((o) => o.area_origem === 'ia').length
    return [{ area, n: os.length, vencidas: venc.length, viaIA, frase: viaIA ? `${frase} · ${viaIA} com área sugerida (IA)` : frase }]
  })

  return {
    cabecalho: {
      norma: plano.norma.titulo,
      porte: sim ? `distribuidora de ${brlCurto(sim.base)} de receita operacional líquida (ilustrativo)` : 'receita não informada (valores em % da receita)',
      data: dataBR(hojeIso),
      prazosAte: dataBR(hojeIso),
      aviso: AVISO_RELATORIO,
    },
    numeros: {
      exposicao: v ? (v.reais != null ? brlCurto(v.reais) : `${pct(v.pct)} da receita`) : 'a enquadrar',
      porInfracao: `por infração${v?.origem === 'sugerido' ? '*' : ''}`,
      reducao: q ? `−${Math.round(q.reducaoPct)}%` : '—',
      prazo: pz.vencidas > 0 ? { valor: String(pz.vencidas), legenda: textoVencidasComDetalhe({ obrigacoes: pz.vencidas, detalhes: pz.detalhes }).replace(/^\d+ /, '') }
        : pz.proxima ? { valor: `${pz.proxima.dias} dias`, legenda: 'até o próximo prazo' } : { valor: '—', legenda: 'nenhum prazo a vencer' },
    },
    decisoes: decisoesDaSemana(plano.temas, diag, sim, modo).map((t) => ({ nome: t.nome, porque: textoPrazoDoTema(plano, t, hojeIso).toLowerCase() })),
    prontidao: (() => { const p = prontidao(plano, respostas, sim, modo); return p.algumaMarcada ? fraseProntidao(p.geral.x, p.geral.y) : null })(),
    temas, lacunas, areas,
    perguntas: perguntasParaOJuridico(plano, normaDaUrl(), sim, modo, hojeIso),
  }
}
