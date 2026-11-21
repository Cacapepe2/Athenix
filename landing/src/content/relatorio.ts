// "Baixar meu relatório": o relatório de trabalho (impressão/PDF) e as colunas novas do CSV. Tudo vem do plano
// (mesmos números da executiva e do plano completo) e do que a empresa escreveu e marcou no navegador.
// Lógica pura, testada em relatorio.test.ts. Nada sai do navegador.
import { prazos, queda, tituloCurto, valorGeral } from './executivo.ts'
import { provasDoTema, recomendacoesDoTema } from './recomendacoes.ts'
import { decisoesDaSemana, nomeDiag, brlCurto, comAtenuantePct, dataBR, exposicaoTema, ordenarTemas, pct, plano, reaisDe, SIM_INICIAL, type Diagnosticos, type ExtrasCsv, type Modo, type Obrigacao, type Simulacao, type Tema } from './plano.ts'
import type { Respostas } from './respostas.ts'

export const AVISO_RELATORIO = 'Análise regulatória preliminar · não constitui parecer jurídico'

const obrigacoesDoTema = (t: Tema): Obrigacao[] => t.obrigacoes.map((id) => plano.obrigacoes.find((o) => o.id === id)!).filter(Boolean)

/** Colunas novas do CSV do plano: o que já fazem, situação informada, provas marcadas e área sugerida. */
export function extrasDoCsv(r: Respostas, diag: Diagnosticos = {}): ExtrasCsv {
  return {
    colunas: ['o_que_ja_fazemos', 'situacao', 'provas_marcadas', 'area'],
    linha: (t, o) => {
      const marcadas = new Set(r.provas[t.id] ?? [])
      const texto = provasDoTema(plano, obrigacoesDoTema(t)).filter((p) => marcadas.has(p.id)).map((p) => p.texto).join('; ')
      return [r.jaFazemos[t.id] ?? '', diag[t.id] ? nomeDiag(diag[t.id]) : '', texto, o.area]
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
export interface AreaRelatorio { area: string; n: number; vencidas: number; frase: string }
export interface Relatorio {
  cabecalho: { norma: string; porte: string; data: string; aviso: string }
  numeros: { exposicao: string; porInfracao: string; reducao: string; prazo: { valor: string; legenda: string } }
  decisoes: { nome: string; porque: string }[]
  temas: LinhaTemaRelatorio[]
  lacunas: { nome: string; motivo: string }[]
  areas: AreaRelatorio[]
}

const curta = (t: string, n = 220) => (t.length <= n ? t : `${t.slice(0, n).replace(/\s+\S*$/, '')}…`)

export function montarRelatorio(args: { sim: Simulacao | null; modo: Modo; diag: Diagnosticos; respostas: Respostas; hoje?: Date }): Relatorio {
  const { sim, modo, diag, respostas } = args
  const base = sim ?? SIM_INICIAL
  const v = valorGeral(plano, sim, modo)
  const q = queda(plano, sim, modo)
  const pz = prazos(plano)
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
      prazo: t.prazo_mais_urgente?.texto ?? 'Sem data no texto',
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
    if (d !== 'parcial' && d !== 'nao') return faltam && Object.keys(respostas.provas).length ? [{ nome: t.nome, motivo: `${faltam} prova(s) sem marcar` }] : []
    return [{ nome: t.nome, motivo: `${nomeDiag(d)}${faltam ? ` · ${faltam} prova(s) sem marcar` : ''}` }]
  })

  const lista = plano.analise.areas.lista
  const areas = lista.flatMap<AreaRelatorio>((area) => {
    const os = plano.obrigacoes.filter((o) => o.area === area)
    if (!os.length) return []
    const venc = os.filter((o) => o.situacao === 'vencida').sort((a, b) => (a.prazo.data ?? '').localeCompare(b.prazo.data ?? ''))
    const frase = venc.length ? `${area}: ${os.length} obrigações, ${venc.length} vencidas — comece por ${venc.length > 3 ? 'estas 3' : venc.length === 1 ? 'esta' : `estas ${venc.length}`}: ${venc.slice(0, 3).map((o) => tituloCurto(o)).join('; ')}` : `${area}: ${os.length} obrigações, nenhuma vencida`
    return [{ area, n: os.length, vencidas: venc.length, frase }]
  })

  return {
    cabecalho: {
      norma: plano.norma.titulo,
      porte: sim ? `distribuidora de ${brlCurto(sim.base)} de receita operacional líquida (ilustrativo)` : 'receita não informada (valores em % da receita)',
      data: dataBR((args.hoje ?? new Date()).toISOString().slice(0, 10)),
      aviso: AVISO_RELATORIO,
    },
    numeros: {
      exposicao: v ? (v.reais != null ? brlCurto(v.reais) : `${pct(v.pct)} da receita`) : 'a enquadrar',
      porInfracao: `por infração${v?.origem === 'sugerido' ? '*' : ''}`,
      reducao: q ? `−${Math.round(q.reducaoPct)}%` : '—',
      prazo: pz.vencidas > 0 ? { valor: String(pz.vencidas), legenda: pz.vencidas === 1 ? 'obrigação vencida' : 'obrigações vencidas' }
        : pz.proxima ? { valor: `${pz.proxima.dias} dias`, legenda: 'até o próximo prazo' } : { valor: '—', legenda: 'nenhum prazo a vencer' },
    },
    decisoes: decisoesDaSemana(plano.temas, diag, sim, modo).map((t) => ({ nome: t.nome, porque: t.prazo_mais_urgente?.texto ?? 'sem data no texto' })),
    temas, lacunas, areas,
  }
}
