import { RascunhosAneel } from './RascunhosAneel'
import { rascunhosDoItem } from '../../content/rascunhos-aneel'
import { LinkFonte } from '../ui/LinkFonte'
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode, type Ref } from 'react'
import { AlertTriangle, ArrowDown, ArrowUp, ChevronDown, ClipboardList, Download, FileText, Printer, Sparkles } from 'lucide-react'
import { Logo } from '../ui/Logo'
import { Tag } from '../product/Tag'
import { Chevron } from '../ui/Chevron'
import { AjudaGrupos } from './AjudaGrupos'
import { BlocosObrigacoes } from './BlocosObrigacoes'
import { RespostasProvider, useRespostas } from './Respostas'
import { Relatorio } from './Relatorio'
import { ComparacaoAnterior } from './ComparacaoAnterior'
import { LIMITE_JA_FAZEMOS, type Respostas } from '../../content/respostas'
import { extrasDoCsv } from '../../content/relatorio'
import { recomendacoesDoTema } from '../../content/recomendacoes'
import { ABERTURA_PERGUNTAS, perguntasParaOJuridico } from '../../content/perguntas'
import { CRITERIO_PRONTIDAO, fraseProntidao, prontidao } from '../../content/prontidao'
import { contagemDeEnquadramentos, destaqueDaNorma, idDaObrigacao, tabelaDeGrupos, textoMaiorMulta, textoPrazoDoTema } from '../../content/executivo'
import { rotuloDoGrupo } from '../../content/gravidade'
import {
  brl, brlCurto, comAtenuantePct, csvPlano, dataBR, decisoesDaSemana, exposicaoTema, lacuna, lerReais, manchete, NOTA_ADVERTENCIA, textoVencidas, textoVencidasComDetalhe, nomeDiag,
  normaDaUrl, obrigacao, ordenarTemas, pct, plano, reaisDe, resumoDiagnostico, situacaoPrazo, SIM_INICIAL, textoFaixa,
  type Citacao, type OutroDispositivo, type Diagnostico, type Diagnosticos, type Exposicao, type Manchete, type Medida, type Modo, type Obrigacao, type Simulacao, type Situacao, type Tema,
} from '../../content/plano'

const r = plano.resumo
/** A visão executiva da mesma norma (/demo/executivo, ou com ?norma=). */
const URL_EXECUTIVO = normaDaUrl() === 'rn1137' ? '/demo/executivo' : `/demo/executivo?norma=${normaDaUrl()}`
const semData = r.por_situacao.evento + r.por_situacao.sem_prazo
const kicker = 'text-xs font-semibold text-bronze-deep '
const PRELIMINAR = 'cenário preliminar: inclui sugestões aguardando confirmação'
const ATENUANTES = plano.reducao.medidas.filter((m) => m.cenario)
const ATEN_I = ATENUANTES.find((m) => m.cenario === 'espontanea')
const ATEN_II = ATENUANTES.find((m) => m.cenario === 'ate_tn')
// Terracota só no fundo das ações principais, no porte escolhido e em etiquetas muito relevantes
// (data-acento). Texto, bordas, links e foco ficam no azul escuro do site (contrastes em index.css).
// No diagnóstico tudo é azul, menos os clicáveis: botões em terracota (principal preenchido, secundário claro).
const BOTAO_ACENTO = 'inline-flex min-h-11 cursor-pointer items-center gap-2 bg-acento-escuro px-5 text-sm font-semibold text-white hover:bg-acento-hover'
const BOTAO_DIAG_SEC = 'inline-flex min-h-11 cursor-pointer items-center gap-2 border border-acento-escuro bg-acento-claro px-5 text-sm font-semibold text-acento-escuro hover:bg-acento-escuro hover:text-white print:hidden'
const BOTAO_SEC = 'inline-flex min-h-11 cursor-pointer items-center gap-2 border border-slate-blue/40 bg-white px-5 text-sm font-medium text-slate-blue hover:border-slate-blue hover:bg-slate-blue/5'
const LINK = 'font-semibold text-slate-blue underline decoration-slate-blue/40 underline-offset-4 hover:decoration-slate-blue'
// Linha clicável de um <details>: borda, fundo ao passar o mouse e chevron que gira (index.css).
const SUMARIO = 'flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-slate-blue/30 bg-white px-4 py-2 font-semibold text-slate-blue hover:border-slate-blue hover:bg-slate-blue/5'

// Receita simulada (null: valor digitado inválido, mostra só percentuais) e modo do cenário. Nada sai do navegador.
const Cenario = createContext<{ sim: Simulacao | null; modo: Modo; relatorio: () => void }>({ sim: SIM_INICIAL, modo: 'preliminar', relatorio: () => {} })

function baixarCsv(diag: Diagnosticos, sim: Simulacao | null, respostas: Respostas) {
  const url = URL.createObjectURL(new Blob([csvPlano(diag, sim, extrasDoCsv(respostas, diag))], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: `athenix-plano-${normaDaUrl()}-ilustrativo.csv` })
  a.click()
  URL.revokeObjectURL(url)
}

/** "R$ 50 milhões" com receita; "1,5% da receita" sem receita válida. */
const valor = (e: Exposicao) => (e.reais != null ? brl(e.reais) : `${pct(e.pct)} da receita`)
const valorCurto = (e: Exposicao) => (e.reais != null ? brlCurto(e.reais) : `${pct(e.pct)} da receita`)
const GRAVIDADE = ['I', 'II', 'III', 'IV', 'V']
const maisGrave = (gs: string[]) => [...gs].sort((a, b) => GRAVIDADE.indexOf(b) - GRAVIDADE.indexOf(a))[0]
/** Porte escolhido em palavras: faixa do topo ou receita informada. */
const nomePorte = (s: Simulacao | null) => {
  const f = s && plano.simulador.faixas.find((x) => x.base === s.base)
  return f ? `${f.rotulo} (~${brlCurto(f.base)} de receita)` : s ? `receita informada de ${brlCurto(s.base)}` : 'receita a informar'
}

/** Marca de valor que vem de sugestão (hachurada; o texto diz o mesmo, sem depender de cor). */
function Sugerido({ texto = 'sugerido' }: { texto?: string }) {
  return <span className="hachura-leve inline-flex items-center rounded-md border border-slate-blue/50 px-2 py-0.5 text-xs font-medium text-obsidian">{texto}</span>
}

/** Manchete: a maior exposição por infração entre os temas vencidos (nunca soma). */
/** Redação de prazo com possível erro na própria norma: o texto literal, a leitura mais provável e a fonte do
 *  esclarecimento, quando houver um confirmado. Nunca é correção automática. */
function ErrosMateriais() {
  return <ul className="space-y-3">{(plano.erros_materiais ?? []).map((e) => (
    <li key={e.obrigacao} className="border-[length:var(--borda-forte)] border-obsidian p-3">
      <p className="font-semibold"><LinkFonte sha256={plano.norma.sha256} trecho={e.trecho}>{e.dispositivo}</LinkFonte>: “{e.trecho}” · {e.problema}</p>
      <p>Leitura mais provável: <strong>{e.leitura_provavel}</strong> · <Tag kind="pending" label={e.rotulo} /></p>
      <p className="text-sm">{e.esclarecimento ?? `Sugestão: ${e.sugestao}.`}</p>
      {plano.obrigacoes.filter((o) => o.id === e.obrigacao && o.esclarecimento).map((o) => <p key={o.id} className="text-xs"><LinkFonte sha256={o.esclarecimento!.fonte.sha256} trecho={o.esclarecimento!.fonte.trecho}>Esclarecimento oficial da ANEEL</LinkFonte></p>)}
    </li>))}</ul>
}

function TextoManchete({ m }: { m: Manchete }) {
  const temas = `${m.temasVencidos} ${m.temasVencidos === 1 ? 'tema já vencido' : 'temas já vencidos'}`
  if (m.temasVencidos === 0) return <>Nenhum tema vencido em aberto</>
  return m.maximo ? <>Até <span className="whitespace-nowrap text-slate-blue">{valorCurto(m.maximo)}</span> por infração em {temas}</> : <>Exposição a enquadrar em {temas}</>
}

export function PlanoPage() {
  const [diag, setDiag] = useState<Diagnosticos>({})
  const [sim, setSim] = useState<Simulacao | null>(SIM_INICIAL)
  const [modo, setModo] = useState<Modo>('preliminar')
  // Diagnóstico gerado na própria página (contagem de cliques: cada clique rola até ele de novo).
  const [geracao, setGeracao] = useState(0)
  const [soDiagnostico, setSoDiagnostico] = useState(false)
  const [imprimindo, setImprimindo] = useState(() => typeof location !== 'undefined' && new URLSearchParams(location.search).has('relatorio'))
  const fimRelatorio = useCallback(() => {
    setImprimindo(false)
    const q = new URLSearchParams(location.search)
    const tinha = q.has('relatorio')
    q.delete('relatorio')
    if (tinha) history.replaceState(history.state, '', `${location.pathname}${q.size ? `?${q}` : ''}${location.hash}`)
  }, [])
  const refDiag = useRef<HTMLElement>(null)
  const temas = useMemo(() => ordenarTemas(plano.temas, diag, sim, modo), [diag, sim, modo])
  const decisoes = decisoesDaSemana(plano.temas, diag, sim, modo)
  const m = manchete(plano.temas, diag, sim, modo)
  const gap = lacuna(plano.temas, diag)
  // Escala das barras: a maior exposição entre os temas visíveis vale 100%. Relativa (e não contra
  // os 3% do teto legal) para que as diferenças entre temas fiquem legíveis; o número vem escrito ao lado.
  const maiorPct = Math.max(0, ...temas.map((t) => exposicaoTema(t, sim, modo)?.pct ?? 0))
  // Impressão: só o resumo (topo e temas; com diagnóstico gerado, topo e diagnóstico). Análises e detalhes ficam recolhidos.
  const marcar = (id: string, d: Diagnostico) => setDiag((atual) => ({ ...atual, [id]: d }))
  const gerado = geracao > 0
  useEffect(() => {
    if (!geracao) return
    refDiag.current?.scrollIntoView({ block: 'start' })
    refDiag.current?.focus({ preventScroll: true })
  }, [geracao])
  // Âncora #obrigacao-<id>: ao carregar, ao clicar num link com ela ou ao mudar o hash, abre o tema e a obrigação.
  useEffect(() => {
    abrirObrigacao(location.hash)
    const clique = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
      const href = (e.target as Element | null)?.closest?.('a[href^="#obrigacao-"]')?.getAttribute('href')
      if (!href || !document.getElementById(href.slice(1))) return
      e.preventDefault() // antes do handler de âncoras do App, que rolaria até um item ainda recolhido
      history.pushState(null, '', href)
      abrirObrigacao(href)
    }
    const hash = () => abrirObrigacao(location.hash)
    document.addEventListener('click', clique, true)
    window.addEventListener('hashchange', hash)
    return () => { document.removeEventListener('click', clique, true); window.removeEventListener('hashchange', hash) }
  }, [])
  useEffect(() => {
    if (!soDiagnostico) return
    const fim = () => setSoDiagnostico(false)
    window.addEventListener('afterprint', fim)
    window.print()
    return () => window.removeEventListener('afterprint', fim)
  }, [soDiagnostico])

  return <RespostasProvider norma={normaDaUrl()}><Cenario.Provider value={{ sim, modo, relatorio: () => setImprimindo(true) }}>
    <header className="border-b border-line bg-ivory print:hidden"><div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-8"><a href="/" aria-label="Athenix, voltar ao início"><Logo /></a><nav aria-label="Páginas da demonstração" className="flex flex-wrap items-center justify-end gap-x-5 gap-y-1"><a href={URL_EXECUTIVO} className={`inline-flex min-h-11 items-center text-sm ${LINK}`}>Visão executiva →</a><a href="/" className={`inline-flex min-h-11 items-center text-sm ${LINK}`}>← Voltar ao site</a></nav></div></header>
    <main id="plano" className={`mx-auto max-w-7xl space-y-14 px-4 pt-6 pb-8 sm:px-8 sm:pt-10 md:pb-28 print:pb-10 ${soDiagnostico ? 'so-diagnostico' : ''} ${imprimindo ? 'so-relatorio' : ''}`}>
      <section aria-labelledby="titulo-plano" className="space-y-6">
        <p className={kicker}>Plano de ação · RN 1.137/2025 · {plano.perfil.rotulo.toLowerCase()} (não é empresa real)</p>
        <Porte setSim={setSim} />
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-2xl border border-slate-blue/40 border-l-4 border-l-slate-blue bg-acento-claro py-2 pr-4 pl-3 text-sm text-obsidian print:hidden">
          <span data-acento="etiqueta" className="inline-flex shrink-0 items-center bg-acento-escuro px-3 py-1 text-xs leading-none font-bold text-white ">Novo</span>
          <span className="min-w-0 lg:hidden">Marque os temas e gere o diagnóstico.</span>
          <span className="hidden min-w-0 lg:inline">Abaixo dos temas há um card de diagnóstico com o resultado ao lado: marque a situação de cada tema e gere aqui mesmo.</span>
          <a href="#seu-diagnostico" className={`inline-flex min-h-11 items-center gap-1.5 whitespace-nowrap ${LINK}`}>Ir para o diagnóstico<ArrowDown aria-hidden="true" className="h-4 w-4 shrink-0" /></a>
        </p>

        <div className="grid items-start gap-5 lg:grid-cols-[1.45fr_1fr]">
          <div className="space-y-3">
          <div className="rounded-2xl border border-line bg-white p-5 sm:p-7">
            <p className="flex flex-wrap items-center gap-2 text-sm text-ink-soft">
              <Tag kind="pending" label="preliminar" />
              <span>Distribuidora de {sim ? brlCurto(sim.base) : 'receita a informar'} · RN 1.137/2025</span>
            </p>
            <h1 id="titulo-plano" className="font-display mt-3 text-[1.75rem] leading-tight sm:text-[2.6rem] sm:leading-[1.12]"><TextoManchete m={m} /></h1>
            <p className="mt-2 text-sm text-ink-soft">{textoVencidasComDetalhe({ obrigacoes: m.obrigacoesVencidas, detalhes: m.detalhesVencidos })} · datas provisórias · os valores não se somam</p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              {modo === 'preliminar' && m.sugeridos > 0 && <Sugerido texto={PRELIMINAR} />}
              {modo === 'confirmados' && <span className="text-sm text-ink-soft">Só enquadramentos que o texto da obrigação nomeia.</span>}
              <button type="button" aria-pressed={modo === 'confirmados'} onClick={() => setModo(modo === 'preliminar' ? 'confirmados' : 'preliminar')} className={`${BOTAO_SEC} print:hidden`}>
                {modo === 'preliminar' ? 'Mostrar só identificados no texto' : 'Voltar ao cenário preliminar'}
              </button>
            </div>
          </div>
          <p className="px-1 text-sm text-ink-soft">{r.aplicaveis} obrigações para distribuidoras · {r.por_situacao.vencida} com prazo vencido · {r.por_situacao['90dias']} vencem em 90 dias · {r.por_situacao.recorrente} recorrentes · {semData} sem data ({r.por_situacao.evento} dependem de evento)</p>
          </div>

          <section aria-labelledby="decisoes" className="rounded-2xl border border-line bg-white p-5 sm:p-7">
            <h2 id="decisoes" className="font-display text-2xl sm:text-3xl">{`${decisoes.length} ${decisoes.length === 1 ? 'decisão' : 'decisões'} para esta semana`}</h2>
            <ol className="mt-5 space-y-4">
              {decisoes.map((t, n) => { const e = exposicaoTema(t, sim, modo); return <li key={t.id} className="flex gap-3">
                <span aria-hidden="true" className="grid h-8 w-8 shrink-0 place-items-center bg-slate-blue font-semibold text-ivory">{n + 1}</span>
                <div className="-mt-1.5 min-w-0">
                  <a href={`#tema-${t.id}`} className={`inline-block py-3 leading-snug ${LINK}`}>{t.nome}<ArrowDown aria-hidden="true" className="ml-1 inline h-4 w-4 align-[-0.15em]" /></a>
                  <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
                    <span>{e ? <>até <strong>{valor(e)}</strong> por infração</> : 'exposição a enquadrar'}{t.contagem.vencida > 0 && <> · {textoVencidas(t.contagem.vencida)}</>}</span>
                    <span aria-hidden="true" className="text-ink-soft">·</span>
                    <span className="text-ink-soft">{situacaoPrazo(t)}</span>
                    {e?.origem === 'sugerido' && <Sugerido />}
                  </p>
                </div>
              </li> })}
            </ol>
            <p className="mt-5 border-t border-line pt-4 text-sm text-ink-soft">Designar quem confirma o enquadramento: confirmar enquadramentos libera o cálculo de {plano.decisoes.confirmar.temas_sem_calculo_confirmado} temas.</p>
          </section>
        </div>
      </section>

      <Prontidao sim={sim} modo={modo} />

      <BlocosObrigacoes sim={sim} modo={modo} />

      <section aria-labelledby="temas" className={gerado ? 'print:hidden' : ''}>
        <p className={kicker}>Plano por tema</p>
        <h2 id="temas" className="font-display mt-2 text-3xl sm:text-4xl">Temas por valor em risco</h2>
        <details className="mt-3 max-w-3xl text-sm print:hidden">
          <summary className={`${SUMARIO} inline-flex text-sm`}>Como ordenamos<Chevron /></summary>
          <p className="mt-2 leading-relaxed text-ink-soft">{plano.regra_ordem}</p>
        </details>
        <ol className="mt-6 space-y-5">{temas.map((t, n) => <CartaoTema key={t.id} tema={t} posicao={n + 1} diag={diag[t.id]} marcar={marcar} maiorPct={maiorPct} />)}</ol>
      </section>

      {/* Diagnóstico: card de controles à esquerda e painel de resultado à direita (empilhados abaixo de 1024 px).
          Na impressão sai só o resultado gerado; sem resultado, a seção inteira fica fora do papel. */}
      <section id="seu-diagnostico" aria-labelledby="titulo-seu-diagnostico" className={`grid scroll-mt-6 grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] print:block ${gerado ? '' : 'print:hidden'}`}>
        <ControlesDiagnostico diag={diag} gap={gap} gerar={() => setGeracao((g) => g + 1)} />
        <div id="painel-diagnostico" className="min-w-0">
          {gerado
            ? <DiagnosticoGerado ref={refDiag} diag={diag} temas={temas} decisoes={decisoes} m={m} imprimir={() => setSoDiagnostico(true)} fechar={() => { setGeracao(0); document.getElementById('seu-diagnostico')?.scrollIntoView({ block: 'start' }) }} />
            : <div className="flex min-h-64 flex-col items-center justify-center gap-3 rounded-2xl border-2 border-slate-blue bg-diag-fundo p-6 text-center text-slate-blue print:hidden">
              <FileText aria-hidden="true" className="h-8 w-8" />
              <p className="max-w-md text-base">O resultado aparece aqui: manchete, {decisoes.length} {decisoes.length === 1 ? 'decisão' : 'decisões'} e os temas em ordem.</p>
            </div>}
        </div>
      </section>

      <div className="space-y-4 print:hidden">
        <Expansivel id="reduzir" titulo="Como reduzir a exposição" resumo="atenuantes do art. 24 da REN 846, regras comuns e valores por tema">{() => <ComoReduzir temas={temas} />}</Expansivel>
        <Expansivel id="linha" titulo="Quando cada coisa vence" resumo={`${r.por_situacao.vencida} vencidas, ${r.por_situacao['90dias']} em 90 dias, ${r.por_situacao.recorrente} recorrentes, ${semData} sem data`}>{() => <LinhaDoTempo />}</Expansivel>
        {!!plano.erros_materiais?.length && <Expansivel id="erros-materiais" titulo="Possíveis erros materiais da norma" resumo={`${plano.erros_materiais.length} ${plano.erros_materiais.length === 1 ? 'redação de prazo' : 'redações de prazo'} com possível erro na própria norma; leitura mais provável a confirmar`}>{() => <ErrosMateriais />}</Expansivel>}
        <Expansivel id="outros" titulo="Outros dispositivos relevantes" resumo={`${plano.outros_dispositivos.length + plano.sem_dever_identificado.length} dispositivos fora da contagem principal (inclui faculdades, deveres condicionais e regras de transição)`}>{() => <OutrosDispositivos />}</Expansivel>
        <Expansivel id="metodo" titulo="Como chegamos aqui" resumo="contagens, prazos, cálculo da exposição, premissas e fontes">{() => <Metodo />}</Expansivel>
        <Expansivel id="perguntas-juridico" titulo="Perguntas para levar ao jurídico" resumo="geradas do que o Athenix marca como incerto: enquadramentos, redações do art. 11, XXIII, excludentes e prazos que dependem da ANEEL">{() => <PerguntasJuridico />}</Expansivel>
        <Expansivel id="como-calculamos" titulo="Como calculamos" resumo="grupos de gravidade, teto de cada um e contagem de deveres">{() => <ComoCalculamos />}</Expansivel>
        <Expansivel id="referencia" titulo="Referência do setor" resumo={`autos de infração publicados em distribuição (${plano.referencia_escala.autos}, amostra pequena)`}>{() => <ReferenciaSetor />}</Expansivel>
      </div>
      <div className="print:hidden"><button type="button" onClick={() => setImprimindo(true)} className={BOTAO_ACENTO}><FileText aria-hidden="true" className="h-4 w-4" />Baixar meu relatório</button> <span className="text-sm">Página para imprimir ou salvar em PDF, com o que vocês escreveram e marcaram. Nada é enviado.</span></div>
      <footer className="border-t border-line pt-6 text-sm text-ink-soft">{plano.aviso} Iniciativa em validação. Valores ilustrativos, que não indicam descumprimento de uma empresa real. Não constitui parecer jurídico. <a className={`ml-2 inline-flex min-h-11 items-center ${LINK} print:hidden`} href="/">Voltar à Athenix</a></footer>
    </main>
    <Relatorio ativo={imprimindo} fim={fimRelatorio} diag={diag} sim={sim} modo={modo} />
    <div role="note" className="z-30 border-t md:fixed md:inset-x-0 md:bottom-0 border-line bg-obsidian/95 px-4 py-2.5 text-center text-xs leading-snug text-ivory print:hidden">
      Iniciativa em validação · valores ilustrativos · não constitui parecer jurídico
    </div>
  </Cenario.Provider></RespostasProvider>
}

/** Abre o <details> do tema e o da obrigação do hash, rola até ela e dá foco com realce azul (index.css). */
function abrirObrigacao(hash: string) {
  if (!hash.startsWith('#obrigacao-')) return
  const alvo = document.getElementById(decodeURIComponent(hash.slice(1)))
  if (!alvo) return
  for (let d = alvo.closest('details'); d; d = d.parentElement?.closest('details') ?? null) d.open = true
  const proprio = alvo.querySelector('details')
  if (proprio) proprio.open = true
  document.querySelectorAll('[data-realce]').forEach((x) => x.removeAttribute('data-realce'))
  alvo.setAttribute('data-realce', '')
  alvo.tabIndex = -1
  // Espera o React montar o detalhe (onToggle) antes de rolar.
  requestAnimationFrame(() => requestAnimationFrame(() => { alvo.scrollIntoView({ block: 'start' }); alvo.focus({ preventScroll: true }) }))
}

/** Card de controles do diagnóstico (à esquerda do painel de resultado; no celular, acima dele). Não acompanha a rolagem. */
function ControlesDiagnostico({ diag, gap, gerar }: { diag: Diagnosticos; gap: ReturnType<typeof lacuna>; gerar: () => void }) {
  const { sim } = useContext(Cenario)
  const { respostas } = useRespostas()
  const marcados = plano.temas.length - gap.semResposta
  return <div className="rounded-2xl border-2 border-slate-blue bg-diag-fundo p-5 text-obsidian sm:p-6 print:hidden">
    <h2 id="titulo-seu-diagnostico" className="font-display flex items-center gap-3 text-2xl text-slate-blue">
      <span aria-hidden="true" className="grid h-10 w-10 shrink-0 place-items-center bg-slate-blue text-white"><ClipboardList className="h-5 w-5" /></span>
      Diagnóstico da regulação
    </h2>
    <p className="mt-3 text-sm">Marque a situação em cada tema acima e gere o resultado aqui, na própria página. Nada é enviado.</p>
    <dl className="mt-4 space-y-3 text-sm">
      <div><dt className="text-ink-soft">Porte</dt><dd className="font-semibold">{nomePorte(sim)} <a href="#porte" className={`inline-flex min-h-11 items-center ${LINK}`}>alterar no topo</a></dd></div>
      <div><dt className="text-ink-soft">Situação por tema</dt>
        <dd aria-live="polite">{marcados === 0 ? <>Nenhum tema marcado ainda.</> : <>{marcados} de {plano.temas.length} temas marcados. Lacuna: <strong>{gap.nao} obrigações</strong> em temas que vocês não atendem e <strong>{gap.parcial}</strong> em temas parciais.</>}</dd></div>
    </dl>
    <p className="mt-3 text-xs text-ink-soft">“Já temos”, “Parcial” ou “Não temos” em cada tema. As marcações ficam só nesta aba. O texto de “O que sua empresa já faz” fica só no seu navegador.</p>
    <button type="button" onClick={gerar} aria-controls="painel-diagnostico" className="mt-4 inline-flex min-h-12 w-full cursor-pointer items-center justify-center gap-2 bg-acento px-5 text-[1.1875rem] font-bold text-white hover:bg-acento-hover"><FileText aria-hidden="true" className="h-5 w-5" />Gerar diagnóstico</button>
    <div className="mt-3 grid gap-2">
      <button type="button" onClick={() => baixarCsv(diag, sim, respostas)} className={`${BOTAO_DIAG_SEC} justify-center`}><Download aria-hidden="true" className="h-4 w-4" />Baixar planilha (CSV)</button>
      <button type="button" onClick={() => window.print()} className={`${BOTAO_DIAG_SEC} justify-center`}><Printer aria-hidden="true" className="h-4 w-4" />Imprimir ou salvar PDF</button>
    </div>
  </div>
}

/** Diagnóstico gerado no navegador, em forma de boletim. Nada é enviado. */
function DiagnosticoGerado({ ref, diag, temas, decisoes, m, imprimir, fechar }: { ref: Ref<HTMLElement>; diag: Diagnosticos; temas: Tema[]; decisoes: Tema[]; m: Manchete; imprimir: () => void; fechar: () => void }) {
  const { sim, modo, relatorio } = useContext(Cenario)
  const { respostas } = useRespostas()
  const gap = lacuna(plano.temas, diag)
  const algumSugerido = temas.some((t) => exposicaoTema(t, sim, modo)?.origem === 'sugerido')
  return <section ref={ref} id="diagnostico-gerado" tabIndex={-1} aria-labelledby="titulo-diagnostico" className="rounded-2xl border-2 border-slate-blue bg-diag-fundo p-5 text-obsidian sm:p-8 print:border-0 print:bg-white print:p-0 print:shadow-none">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <p className="text-xs font-bold text-slate-blue ">Diagnóstico da regulação</p>
      <div className="flex flex-wrap gap-2 print:hidden">
        <button type="button" onClick={imprimir} className={BOTAO_ACENTO}><Printer aria-hidden="true" className="h-4 w-4" />Imprimir este diagnóstico</button>
        <button type="button" onClick={() => baixarCsv(diag, sim, respostas)} className={BOTAO_DIAG_SEC}><Download aria-hidden="true" className="h-4 w-4" />Planilha (CSV)</button>
        <button type="button" onClick={relatorio} className={BOTAO_DIAG_SEC}><FileText aria-hidden="true" className="h-4 w-4" />Baixar meu relatório</button>
        <button type="button" onClick={fechar} className={BOTAO_DIAG_SEC}>Fechar</button>
      </div>
    </div>
    <h2 id="titulo-diagnostico" className="font-display mt-3 text-[2rem] text-obsidian leading-tight sm:text-[2.6rem] sm:leading-[1.1]"><TextoManchete m={m} /></h2>
    <p className="mt-3 text-sm text-ink-soft">Data de referência {dataBR(plano.perfil.data_referencia)} · Porte: {nomePorte(sim)} · RN 1.137/2025 · {modo === 'preliminar' ? 'cenário preliminar' : 'só enquadramentos identificados no texto'} · {plano.perfil.rotulo.toLowerCase()} (não é empresa real)</p>
    <p className="mt-5 max-w-4xl text-lg leading-relaxed">{resumoDiagnostico(plano.temas, diag, sim, modo)}</p>
    {algumSugerido && <p className="mt-3 flex flex-wrap items-center gap-2 text-sm"><Tag kind="ai" label="Interpretação da IA · aguarda revisão humana" /><span className="text-ink-soft">Valores marcados “sugerido” usam o enquadramento sugerido pela IA ({PRELIMINAR}).</span></p>}

    <div className="mt-8 grid items-start gap-6 xl:grid-cols-[1.3fr_1fr]">
      <div><h3 className="font-display text-2xl text-slate-blue">{`${decisoes.length} ${decisoes.length === 1 ? 'decisão' : 'decisões'} para esta semana`}</h3>
        <ol className="mt-3 list-decimal space-y-2 pl-5">{decisoes.map((t) => { const e = exposicaoTema(t, sim, modo); return <li key={t.id}><a href={`#tema-${t.id}`} className={`inline-block py-2.5 ${LINK} print:py-0 print:no-underline`}>{t.nome}<ArrowDown aria-hidden="true" className="ml-1 inline h-4 w-4 align-[-0.15em] print:hidden" /></a>
          <span className="block text-sm">{e ? <>até <strong>{valor(e)}</strong> por infração</> : 'exposição a enquadrar'} · {situacaoPrazo(t)} {e?.origem === 'sugerido' && <Sugerido />}</span></li> })}</ol></div>
      <div className="rounded-xl border border-slate-blue/30 bg-diag-caixa p-4 text-sm print:bg-white"><h3 className="font-semibold text-slate-blue">Lacuna informada</h3>
        {gap.semResposta === plano.temas.length ? <><p className="mt-1 font-semibold">Nenhum tema marcado ainda; marque a situação de cada tema para ver a lacuna.</p>
          <p className="mt-1">Por enquanto, o diagnóstico mostra só a exposição, sem a situação da empresa. Depois de marcar, gere de novo.</p>
          <a href="#temas" className={`mt-2 ${BOTAO_ACENTO} print:hidden`}>Marcar os temas<ArrowUp aria-hidden="true" className="h-4 w-4" /></a></>
          : <p className="mt-1"><strong>{gap.nao}</strong> obrigações em temas que vocês não atendem, <strong>{gap.parcial}</strong> em temas parciais e <strong>{gap.atendido}</strong> em temas atendidos. {gap.semResposta} {gap.semResposta === 1 ? 'tema' : 'temas'} sem resposta.</p>}
      </div>
    </div>

    <h3 className="font-display mt-10 text-2xl text-slate-blue">Temas na ordem de prioridade</h3>
    <ol className="mt-3 space-y-5">{temas.map((t, n) => { const e = exposicaoTema(t, sim, modo); return <li key={t.id} className="border-t border-line pt-4">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <p className="font-semibold">{n + 1}. {t.nome}</p>
        <p className="flex flex-wrap items-center gap-2 text-sm">{e ? <span>até <strong>{valor(e)}</strong> por infração</span> : <span>exposição a enquadrar</span>}{e?.origem === 'sugerido' && <Sugerido />}</p>
      </div>
      <p className="mt-1 text-sm text-ink-soft">{situacaoPrazo(t)}{t.contagem.vencida > 0 && <> · {textoVencidas(t.contagem.vencida)}</>} · {t.n} {t.n === 1 ? 'obrigação' : 'obrigações'} · Situação informada: <strong className="text-obsidian">{nomeDiag(diag[t.id])}</strong></p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{t.principais.map((id) => { const o = obrigacao(id); return <li key={id}><Titulo o={o} /> <span className="text-xs text-ink-soft">· <LinkFonte sha256={plano.norma.sha256} trecho={o.trecho}>{o.dispositivo ?? 'dispositivo a confirmar'}</LinkFonte> · {o.prazo.texto}</span></li> })}</ul>
    </li> })}</ol>
    <p className="mt-8 border-t border-line pt-4 text-xs leading-relaxed text-ink-soft">Valores por infração, que não se somam; {NOTA_ADVERTENCIA}. Pior caso, sem agravantes; datas provisórias. Calculado no seu navegador com os dados deste plano: nada foi enviado nem salvo. {plano.aviso} Iniciativa em validação. Não constitui parecer jurídico.</p>
  </section>
}

/** Bloco recolhido: título claro e resumo de uma linha; o conteúdo só é montado ao abrir. */
function Expansivel({ id, titulo, resumo, children }: { id: string; titulo: string; resumo: string; children: () => ReactNode }) {
  const [aberto, setAberto] = useState(false)
  return <section aria-labelledby={id}><details className="group rounded-2xl border border-slate-blue/30 bg-white hover:border-slate-blue open:border-line" onToggle={(e) => setAberto(e.currentTarget.open)}>
    <summary className="flex min-h-11 cursor-pointer items-center gap-3 rounded-2xl p-5 hover:bg-slate-blue/5 sm:px-7">
      <span className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 id={id} className="font-display text-2xl text-obsidian sm:text-3xl">{titulo}</h2>
        <span className="text-sm text-ink-soft">{resumo}</span>
      </span>
      <span className="inline-flex min-h-11 shrink-0 items-center gap-1 border border-slate-blue/40 bg-white px-3 text-sm font-semibold text-slate-blue group-hover:border-slate-blue"><span className="group-open:hidden">Abrir</span><span className="hidden group-open:inline">Fechar</span><ChevronDown aria-hidden="true" className="h-5 w-5 transition-transform group-open:rotate-180" /></span>
    </summary>
    {aberto && <div className="px-5 pb-6 sm:px-7">{children()}</div>}
  </details></section>
}

/** Fonte, SHA-256 e origem da redação da infração citada (conferidas pelo export), no formato das atenuantes. */
function ProvInfracao({ d }: { d: string }) {
  const i = plano.infracoes[d]
  if (!i) return null
  return <span className="mt-1 block break-all text-xs text-ink-soft">Fonte: <LinkFonte sha256={i.fonte.sha256} trecho={i.trecho}>{i.fonte.titulo}</LinkFonte> ({i.fonte.arquivo}) · SHA-256 {i.fonte.sha256} · redação: {i.origem_da_redacao}{i.conferido_na_fonte ? ' · trecho conferido no arquivo' : ''}</span>
}

/** As duas redações datadas de um dispositivo, com fonte, vigência e estado. A futura segue incerta. */
function SucessaoNoTempo({ dispositivo }: { dispositivo: string }) {
  const s = plano.sucessao_no_tempo.find((x) => x.dispositivo === dispositivo)
  if (!s) return null
  return <div className="mt-2 rounded-lg border border-pending/50 bg-stone p-3 text-xs">
    <p className="font-semibold text-obsidian">{s.dispositivo}: duas redações em sucessão no tempo (dúvida {s.duvida}, para especialista)</p>
    <ul className="mt-2 space-y-2">{s.redacoes.map((r) => <li key={r.ato}>
      <p className="font-semibold">{r.ato} · {r.vigencia_ate ? `de ${dataBR(r.vigencia_de)} até ${dataBR(r.vigencia_ate)}` : `a partir de ${dataBR(r.vigencia_de)}`} · {r.estado === 'verified' ? 'redação conferida na fonte' : 'INCERTA: não confirmada por leitura independente'}</p>
      <blockquote className="mt-1 border-l-2 border-bronze bg-white p-2 text-sm">“{r.trecho}”</blockquote>
      <p className="mt-1 break-all text-ink-soft"><LinkFonte sha256={r.fonte.sha256} trecho={r.trecho}>{s.dispositivo} · {r.fonte.titulo}</LinkFonte> ({r.fonte.arquivo}) · SHA-256 {r.fonte.sha256}{r.motivo ? ` · ${r.motivo}` : ''}</p>
    </li>)}</ul>
    <p className="mt-2 text-ink-soft">{s.texto_da_duvida}</p>
  </div>
}

/** Faculdades, direitos de terceiros e competências da ANEEL: não entram na contagem de deveres. */
function OutrosDispositivos() {
  const por = (n: OutroDispositivo['natureza']) => [...plano.outros_dispositivos, ...plano.sem_dever_identificado].filter((o) => o.natureza === n)
  const grupos: [OutroDispositivo['natureza'], string][] = [['faculdade', 'Faculdades (a norma diz que pode, não que deve)'], ['direito_de_terceiro', 'Direitos de consumidores e usuários'], ['competencia_aneel', 'Competências da ANEEL'], ['dever_de_outro_agente', 'Deveres de outros agentes (não são da distribuidora)'], ['regra_de_transicao', 'Regras de transição e vigência de outros dispositivos']]
  grupos.push(['sem_dever_identificado', 'Sem dever identificado (lidos pela extração, sem verbo de dever e sem a distribuidora agindo; nada some em silêncio)'])
  grupos.push(['dever_condicional', 'Deveres condicionais (só para quem exercer a faculdade do caput)'])
  return <div className="space-y-5 text-sm">
    <p className="text-ink-soft">Dispositivos lidos pela mesma extração fora da contagem principal e do cálculo de multa. Incluem deveres condicionais, exigíveis apenas se a distribuidora exercer a faculdade do caput. Cada um mostra o trecho literal e o dispositivo.</p>
    {Object.entries(plano.notas_outros).map(([art, nota]) => <p key={art} className="border-[length:var(--borda-forte)] border-obsidian p-3 font-semibold">{art}: {nota}</p>)}
    {grupos.map(([n, titulo]) => por(n).length > 0 && <div key={n}>
      <h3 className="font-semibold">{titulo} <span className="text-ink-soft">({por(n).length})</span></h3>
      <ul className="mt-2 space-y-3">{por(n).map((o) => <li key={o.id}>
        <blockquote className="border-l-2 border-bronze bg-ivory p-3">“{o.trecho ?? 'sem citação verificada'}”</blockquote>
        {o.condicao && <p className="mt-1 text-xs"><strong>{o.condicao.texto}</strong> · <LinkFonte sha256={plano.norma.sha256} trecho={o.condicao.trecho}>{o.condicao.dispositivo}</LinkFonte>: “{o.condicao.trecho}”</p>}
        <p className="mt-1 text-xs text-ink-soft"><LinkFonte sha256={plano.norma.sha256} trecho={o.trecho}>{o.dispositivo ?? 'dispositivo a confirmar'}</LinkFonte> · {o.natureza === 'sem_dever_identificado' ? o.motivo : `sujeito: ${o.sujeito}`}</p>
      </li>)}</ul>
    </div>)}
  </div>
}

function Metodo() {
  const esc = plano.referencia_escala
  return <div className="max-w-3xl space-y-3 text-sm leading-relaxed">
    <p>Contagens: {r.aplicaveis} obrigações para distribuidoras · {r.por_situacao.vencida} com prazo vencido · {r.por_situacao['90dias']} vencem em 90 dias · {r.por_situacao.recorrente} recorrentes · {semData} sem data ({r.por_situacao.evento} dependem de evento).</p>
    <p>A leitura automática da norma identificou {r.identificadas} itens. {r.fora_do_perfil} {r.fora_do_perfil === 1 ? 'vale' : 'valem'} só para transmissoras; {r.outros_dispositivos} ficam fora da contagem principal (incluem deveres condicionais, faculdades e regras de transição: veja “Outros dispositivos relevantes”); os {r.aplicaveis} deveres restantes entram neste plano. Em {r.na_fila} o texto da obrigação nomeia o instrumento de uma infração da REN 846 e o grupo de multa é identificado; {r.a_confirmar} aguardam a confirmação do enquadramento por uma pessoa; {r.sem_multa} não têm multa estimável.</p>
    <p>Os temas seguem as seções da própria norma (por exemplo, “{plano.temas[0].fontes[0]?.titulo}”). Disposições transitórias vão para o tema do primeiro assunto que nomeiam.</p>
    <p>Prazos: calculados pelo motor temporal a partir da publicação ({dataBR(plano.norma.vigencia)}). Ficam provisórios até uma pessoa confirmar a contagem.</p>
    <p>Exposição: teto do grupo de infração (REN 846, Art. 8º) sobre a receita operacional líquida, limitado pelo teto legal. Sem simulação, a receita é a ilustrativa de {brl(plano.perfil.base_reais)}. {plano.perfil.origem_base} Sem faturamento bruto informado, o teto legal pode estar subestimado. A manchete mostra a maior exposição por infração entre os temas já vencidos.</p>
    <p>Cenário preliminar e só identificados no texto: no cenário preliminar (padrão), os enquadramentos sugeridos pela IA também contam, sempre marcados como “sugerido” e com barra hachurada; o cálculo continua sendo o do motor, só com o grupo sugerido. Em “Mostrar só identificados no texto” entram apenas os enquadramentos que o texto da obrigação nomeia. Nenhuma sugestão é confirmada em nome de uma pessoa.</p>
    <p>Porte, no topo da página: Pequena ~{brl(plano.simulador.faixas[0].base)}, Média ~{brl(plano.simulador.faixas[1].base)}, Grande ~{brl(plano.simulador.faixas[2].base)} e Muito grande ~{brl(plano.simulador.faixas[3].base)} de receita operacional líquida anual; em “Ajustar premissas” dá para informar a receita e o faturamento bruto. {plano.simulador.origem_faixas} A conta é a mesma do motor da Athenix (grupos I a V, percentuais da REN 846 e teto legal sobre o faturamento), refeita no seu navegador; um teste automático confere o resultado com o motor.</p>
    <p>Diagnóstico gerado: montado no seu navegador com as mesmas funções da página (ordem dos temas, decisões, manchete, lacuna). Nada é enviado nem salvo.</p>
    <p>Referência do setor: {esc.limites} Unidade: {esc.unidade}.</p>
    <p>Como reduzir a exposição: os textos citados vêm do catálogo de multas extraído do compilado oficial da REN 846 (SHA-256 indicado em cada citação). Os cenários com atenuante são do motor, com o valor base no teto do grupo (pior caso) e sem agravantes. Condição e efeito em linguagem simples são nossa interpretação e aguardam revisão humana. Causas externas só são citadas quando o texto da própria obrigação as prevê.</p>
    <p>Análise regulatória preliminar (em cada tema): tipo da obrigação por regras, com ideias de cumprimento e de evidência em rascunho, e dependências de terceiros só quando o trecho literal da norma as nomeia. Prática conhecida fora do texto da norma aparece separada, com referências públicas e o contraponto.</p>
    {plano.ia && <p><Tag kind="ai" /> {plano.ia.aviso} Modelo {plano.ia.modelo}. {plano.ia.criterio_titulos} Títulos marcados com <Sparkles aria-label="ícone de IA" className="inline h-3 w-3" /> foram resumidos com IA. Enquadramentos: {plano.ia.criterio_enquadramentos.toLowerCase()}</p>}
    <p className="break-all text-xs text-ink-soft">Documento preservado · SHA-256 {plano.norma.sha256} · gerado por {plano.gerado_por} (commit {plano.commit_origem}).</p>
  </div>
}

/** Grupos de gravidade e teto de cada um (com o dispositivo da REN 846), tudo vindo do plano. */
/** Indicador geral de prontidão: só aparece depois de o usuário marcar alguma prova. */
function Prontidao({ sim, modo }: { sim: Simulacao | null; modo: Modo }) {
  const { respostas } = useRespostas()
  const p = prontidao(plano, respostas, sim, modo)
  if (!p.algumaMarcada) return null
  return <p className="border-[length:var(--borda-forte)] border-obsidian p-4 text-lg font-bold print:hidden" aria-live="polite">{fraseProntidao(p.geral.x, p.geral.y)} <a href="#como-calculamos" className={`text-sm ${LINK}`}>como contamos</a></p>
}

/** Perguntas para o jurídico, geradas do que o plano marca como incerto. */
function PerguntasJuridico() {
  const { sim, modo } = useContext(Cenario)
  const qs = perguntasParaOJuridico(plano, normaDaUrl(), sim, modo)
  return <div className="max-w-4xl space-y-3 text-sm">
    <p className="font-semibold">{ABERTURA_PERGUNTAS}</p>
    <ol className="space-y-3">{qs.map((q, i) => <li key={i} className="border-l-[length:var(--borda-titulo)] border-obsidian pl-3.5">
      <p>{q.pergunta}</p><p className="mt-1 text-xs text-ink-soft">{q.dispositivo} · {q.citacao} · {q.fontes.map((f, i) => <span key={i}>{i > 0 && ' · '}<LinkFonte sha256={f.sha256} trecho={f.trecho}>{f.rotulo}</LinkFonte></span>)}</p></li>)}</ol>
    {qs.length === 0 && <p>Nada marcado como incerto neste plano.</p>}
  </div>
}

function ComoCalculamos() {
  const t = tabelaDeGrupos(plano)
  return <div className="max-w-4xl space-y-3 text-sm leading-relaxed">
    <p>{destaqueDaNorma(plano).texto}. {contagemDeEnquadramentos(plano).texto}.</p>
    <p><strong>Prontidão para fiscalização.</strong> {CRITERIO_PRONTIDAO}</p>
    <p>A ANEEL classifica cada infração em 5 grupos de gravidade (REN 846, o regulamento de multas). Cada grupo tem um teto de multa em % da receita da empresa.</p>
    <ul className="grid gap-2 sm:grid-cols-5" aria-label="Teto de multa por grupo">
      {t.grupos.map((g) => <li key={g.grupo} className="border border-line px-3 py-2" title={g.trecho ?? undefined}>
        <span className="block">{g.rotulo}</span>
        <strong className="block">{g.pct != null ? `até ${pct(g.pct)} da receita` : 'sem teto citado'}</strong>
        <span className="block text-xs text-ink-soft">REN 846, <LinkFonte sha256={g.sha256} trecho={g.trecho}>{g.dispositivo ?? 'dispositivo a confirmar'}</LinkFonte></span>
      </li>)}
    </ul>
    {t.tetoLegal && <p>Por infração, nunca somadas. Acima de todos, o limite legal de {t.tetoLegal.pct != null ? pct(t.tetoLegal.pct) : '—'} do faturamento (<LinkFonte sha256={t.tetoLegal.sha256} trecho={t.tetoLegal.trecho}>{t.tetoLegal.dispositivo}</LinkFonte>).</p>}
  </div>
}

function ReferenciaSetor() {
  const esc = plano.referencia_escala
  return <div className="max-w-3xl text-sm">
    <p>Mediana de {esc.autos} autos de infração publicados em distribuição (amostra pequena) ≈ <strong>{brlCurto(esc.mediana_reais)}</strong>; maior na amostra ≈ <strong>{brlCurto(esc.maximo_reais)}</strong>.</p>
    <p className="mt-2">{textoMaiorMulta(plano)} <span className="text-xs text-ink-soft">(fonte: {esc.maior_multa.fonte})</span>.</p>
    <p className="mt-1 text-xs text-ink-soft">{esc.rotulo}. É valor do auto inteiro, que pode reunir várias infrações; não é comparável ao valor por infração. Limites da amostra em “Como chegamos aqui”.</p>
  </div>
}

const numeroBR = (v: number) => v.toLocaleString('pt-BR', { maximumFractionDigits: 2 })

/** Porte no topo; receita e faturamento recolhidos em "Ajustar premissas". A conta roda no navegador. */
function Porte({ setSim }: { setSim: (s: Simulacao | null) => void }) {
  const { sim } = useContext(Cenario)
  const faixas = plano.simulador.faixas
  const [porte, setPorte] = useState(faixas.find((f) => f.base === SIM_INICIAL.base)?.id ?? 'livre')
  const [rol, setRol] = useState(numeroBR(SIM_INICIAL.base))
  const [fat, setFat] = useState('')
  const aplicar = (rolT: string, fatT: string) => {
    const base = lerReais(rolT)
    const faturamento = fatT.trim() ? lerReais(fatT) : null
    setSim(base != null && (faturamento != null || !fatT.trim()) ? { base, faturamento } : null)
  }
  const rolInvalido = lerReais(rol) == null
  const fatInvalido = fat.trim() !== '' && lerReais(fat) == null
  const campo = 'mt-1 min-h-11 w-full rounded-xl border bg-white px-3 text-base tabular-nums'
  return <div className="space-y-3">
    <fieldset id="porte">
      <legend className="flex flex-wrap items-center gap-2 text-sm font-semibold">Porte da distribuidora (receita operacional líquida anual) <Tag kind="estimate" label="Faixa ilustrativa" /></legend>
      <div className="mt-2 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
        {faixas.map((x) => <label key={x.id} className="inline-flex min-h-11 cursor-pointer flex-col items-center justify-center rounded-2xl border border-slate-blue/40 bg-white px-3 py-1 text-center text-sm leading-tight text-obsidian hover:border-slate-blue hover:bg-slate-blue/5 sm:flex-row sm:gap-1 sm:sm:px-4 has-checked:border-transparent has-checked:bg-acento-escuro has-checked:font-semibold has-checked:text-white has-checked:has-checked:hover:bg-acento-escuro has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-slate-blue">
          <input type="radio" className="sr-only" name="porte" value={x.id} checked={porte === x.id} onChange={() => { setPorte(x.id); const t = numeroBR(x.base); setRol(t); aplicar(t, fat) }} />
          <span className="font-medium sm:font-normal">{x.rotulo}</span> <span className="text-xs whitespace-nowrap sm:text-sm">~{brlCurto(x.base)}</span>
        </label>)}
      </div>
    </fieldset>
    <details className="max-w-3xl print:hidden">
      <summary className={`${SUMARIO} text-sm`}><span className="min-w-0">Ajustar premissas{porte === 'livre' && sim ? ` · receita informada: ${brl(sim.base)}` : ''}</span><Chevron /></summary>
      <div className="mt-2 grid gap-4 rounded-xl border border-line bg-white p-4 sm:grid-cols-2">
        <label className="block text-sm"><span className="font-semibold">Receita operacional líquida, 12 meses (R$)</span> <Tag kind="review" label="Premissa do usuário" />
          <input inputMode="decimal" autoComplete="off" className={`${campo} ${rolInvalido ? 'border-pending' : 'border-line'}`} value={rol} aria-invalid={rolInvalido} aria-describedby="rol-ajuda"
            onChange={(e) => { setRol(e.target.value); setPorte('livre'); aplicar(e.target.value, fat) }} />
          <span id="rol-ajuda" className={`mt-1 block text-xs ${rolInvalido ? 'text-pending' : 'text-ink-soft'}`}>{rolInvalido ? 'Informe um valor em reais, por exemplo 7.500.000.000. Enquanto isso, os valores aparecem em % da receita.' : `Base da multa (REN 846, art. 21): ${brl(lerReais(rol)!)}.`}</span>
        </label>
        <label className="block text-sm"><span className="font-semibold">Faturamento bruto, 12 meses (R$, opcional)</span> <Tag kind="review" label="Premissa do usuário" />
          <input inputMode="decimal" autoComplete="off" className={`${campo} ${fatInvalido ? 'border-pending' : 'border-line'}`} value={fat} placeholder="em branco" aria-invalid={fatInvalido} aria-describedby="fat-ajuda"
            onChange={(e) => { setFat(e.target.value); aplicar(rol, e.target.value) }} />
          <span id="fat-ajuda" className={`mt-1 block text-xs ${fatInvalido ? 'text-pending' : 'text-ink-soft'}`}>{fatInvalido ? 'Valor inválido: deixe em branco ou informe em reais.' : 'Usado só no teto legal (Lei 9.427/1996, art. 3º, X). Em branco, o teto legal é aplicado sobre a receita líquida e pode estar subestimado (dúvida D6).'}</span>
        </label>
        <p className="text-xs text-ink-soft sm:col-span-2">Estimativa com premissas do usuário, sem agravantes. A conta roda no seu navegador: nada é enviado nem salvo.</p>
      </div>
    </details>
  </div>
}

/** "O que recomendamos": ações, provas, defesa, "Evite" e o efeito de agir; e o campo "O que sua empresa já faz". */
function Recomendamos({ t }: { t: Tema }) {
  const { sim, modo } = useContext(Cenario)
  const { respostas, persistente, escrever, marcarProva } = useRespostas()
  const rec = recomendacoesDoTema(plano, t, sim, modo)
  const medida = ATENUANTES.find((m) => m.dispositivo === rec.efeito?.dispositivo)
  const pr = prontidao(plano, respostas, sim, modo)
  const marcadas = respostas.provas[t.id] ?? []
  const texto = respostas.jaFazemos[t.id] ?? ''
  return <section aria-labelledby={`rec-${t.id}`} className="mt-5 border-[length:var(--borda-forte)] border-obsidian p-4 sm:p-5">
    <h4 id={`rec-${t.id}`} className="flex flex-wrap items-center gap-2 text-xl font-bold">O que recomendamos <Tag kind="review" label="Sugestão" /></h4>
    {rec.acoes.length ? <ol className="mt-3 space-y-2">{rec.acoes.map((a) => <li key={a} className="border-l-[length:var(--borda-titulo)] border-obsidian pl-3.5 text-base leading-snug">{a}</li>)}</ol>
      : <p className="mt-3 text-sm">Recomendação em revisão: a IA não deu uma ação de nível gerencial válida para este tema.</p>}
    {rec.operacionais.length > 0 && <details className="mt-3 text-sm print:hidden"><summary className="min-h-11 cursor-pointer py-2 font-semibold underline underline-offset-4">Detalhe operacional (sugestão)</summary>
      <ul className="mt-1 list-disc space-y-1 pl-5">{rec.operacionais.map((a) => <li key={a}>{a}</li>)}</ul></details>}
    <div className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
      <div><h5 className="font-bold">O que guardar como prova</h5>
        {rec.provas.length ? <ul className="mt-1 space-y-1">{rec.provas.map((x) => <li key={x.id}><label className="flex min-h-11 cursor-pointer items-start gap-2 py-1">
          <input type="checkbox" className="mt-1 h-5 w-5 shrink-0 accent-[var(--cor-texto)]" checked={marcadas.includes(x.id)} onChange={() => marcarProva(t.id, x.id)} /><span>{x.texto}</span></label></li>)}</ul> : <p className="mt-1">—</p>}
        {rec.provas.length > 0 && <p className="mt-1 text-xs" aria-live="polite">Marque o que vocês já têm. {marcadas.length > 0 ? <strong>Provas em mãos neste tema: {pr.porTema[t.id].x} de {pr.porTema[t.id].y}.</strong> : 'Fica só no seu navegador.'}</p>}</div>
      <div className="space-y-3">
        {rec.efeito && <div><h5 className="font-bold">Efeito financeiro de agir</h5>
          <p className="mt-1">Regularizar antes da fiscalização pode reduzir até {pct(rec.efeito.reducaoPct)}{rec.efeito.de != null && rec.efeito.para != null ? ` (${brlCurto(rec.efeito.de)} → ${brlCurto(rec.efeito.para)})` : ''} <span className="text-xs text-ink-soft">(<LinkFonte sha256={medida?.sha256 ?? ''} trecho={medida?.trecho}>{rec.efeito.dispositivo}</LinkFonte> da REN 846; exige cessar a infração e reparar o dano)</span></p></div>}
        {rec.defesa && <div><h5 className="font-bold">Defesa possível</h5><p className="mt-1">{rec.defesa.texto} <span className="text-xs text-ink-soft">({rec.defesa.origem})</span></p></div>}
        {rec.evite && <div><h5 className="font-bold text-evite">Evite</h5><p className="mt-1">{rec.evite} <span className="text-xs text-ink-soft">(Sugestão)</span></p></div>}
      </div>
    </div>
    <div className="mt-4 border-t border-line pt-4 print:hidden">
      <label htmlFor={`ja-${t.id}`} className="text-sm font-bold">O que sua empresa já faz</label>
      <textarea id={`ja-${t.id}`} rows={3} maxLength={LIMITE_JA_FAZEMOS} value={texto} onChange={(e) => escrever(t.id, e.target.value)} aria-describedby={`ja-aj-${t.id}`}
        className="mt-1 block w-full border-[length:var(--borda-forte)] border-obsidian bg-white p-2.5 text-sm" placeholder="Ex.: plano aprovado em 2025, sem revisão anual ainda" />
      <p id={`ja-aj-${t.id}`} className="mt-1 flex flex-wrap justify-between gap-2 text-xs"><span>{texto.length}/{LIMITE_JA_FAZEMOS} · Fica só no seu navegador. Nada é enviado.</span>
        {!persistente && <span role="status" className="font-semibold text-bronze-deep">Este navegador não deixou gravar: o texto se perde ao fechar a página.</span>}</p>
    </div>
  </section>
}

const OPCOES: [Diagnostico, string][] = [['sim', 'Já temos'], ['parcial', 'Parcial'], ['nao', 'Não temos']]

function CartaoTema({ tema: t, posicao, diag, marcar, maiorPct }: { tema: Tema; posicao: number; diag?: Diagnostico; marcar: (id: string, d: Diagnostico) => void; maiorPct: number }) {
  const { sim, modo } = useContext(Cenario)
  const e = exposicaoTema(t, sim, modo)
  const grupo = e && maisGrave(e.origem === 'confirmado' ? t.grupos : t.grupos_sugeridos)
  const cont = (s: Situacao) => t.contagem[s]
  return <li id={`tema-${t.id}`} className={`rounded-2xl border border-line bg-white p-5 sm:p-7 ${diag === 'sim' ? 'opacity-80' : ''}`}>
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex min-w-0 items-start gap-3">
        <span aria-label={`Posição ${posicao}`} className="font-display grid h-10 w-10 shrink-0 place-items-center bg-stone text-xl">{posicao}</span>
        <div className="min-w-0"><h3 className="font-display text-2xl leading-tight">{t.nome}</h3>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-soft">
            <span>{situacaoPrazo(t)}</span><span aria-hidden="true">·</span>
            <span>{t.n} {t.n === 1 ? 'obrigação' : 'obrigações'}</span>
            {grupo && <><span aria-hidden="true">·</span><span className="inline-flex items-center gap-1.5">{rotuloDoGrupo(grupo)}<AjudaGrupos p={plano} /></span>{e!.origem === 'confirmado' ? <span className="bg-slate-blue px-2 py-0.5 text-xs font-medium text-ivory">identificado no texto ({t.na_fila} de {t.n} {t.n === 1 ? 'obrigação' : 'obrigações'})</span> : <Sugerido />}</>}
            {diag === 'sim' && <><span aria-hidden="true">·</span><span>você marcou como já atendido</span></>}
          </p>
        </div>
      </div>
      <fieldset className="print:hidden">
        <legend className="mb-1 text-xs text-ink-soft">Sua situação hoje</legend>
        <div className="inline-flex gap-1 border border-line bg-ivory p-1">
          {OPCOES.map(([v, rotulo]) => <label key={v} className="inline-flex min-h-11 cursor-pointer items-center border border-slate-blue/40 bg-white px-3 text-sm text-obsidian hover:border-slate-blue hover:bg-slate-blue/5 has-checked:border-slate-blue has-checked:bg-slate-blue has-checked:font-semibold has-checked:text-white has-checked:hover:bg-slate-blue has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-slate-blue">
            <input type="radio" className="sr-only" name={`diag-${t.id}`} value={v} checked={diag === v} onChange={() => marcar(t.id, v)} />{rotulo}
          </label>)}
        </div>
      </fieldset>
      <p className="hidden text-sm print:block">Situação informada: {nomeDiag(diag)}</p>
    </div>

    <Recomendamos t={t} />

    <div className="mt-5">
      {e ? <>
        <p className="text-lg"><span className="font-display text-2xl font-semibold sm:text-3xl">até {valor(e)}</span> <span className="text-ink-soft">por infração{t.contagem.vencida > 0 && <> · {textoVencidas(t.contagem.vencida)}</>}</span></p>
        <Escada e={e} maiorPct={maiorPct} />
        <p className="mt-1 text-xs text-ink-soft">{textoFaixa(e.faixa, sim)} ({NOTA_ADVERTENCIA}){e.origem === 'sugerido' ? ` · ${PRELIMINAR}` : ''}</p>
      </> : <p className="text-lg font-semibold">exposição a enquadrar <span className="block text-xs font-normal text-ink-soft">Sem enquadramento identificado nem sugerido: não há valor a mostrar.</span></p>}
    </div>

    <dl className="mt-5 grid gap-4 border-y border-line py-5 text-sm sm:grid-cols-3">
      <div><dt className="text-ink-soft">Prazo mais urgente</dt><dd className="mt-1 font-semibold">{textoPrazoDoTema(plano, t)}</dd>
        <dd className="mt-1 text-xs text-ink-soft">{[cont('vencida') && `${cont('vencida')} vencida(s)`, cont('recorrente') && `${cont('recorrente')} recorrente(s)`, cont('evento') && `${cont('evento')} dependem de evento`, cont('sem_prazo') && `${cont('sem_prazo')} sem prazo`].filter(Boolean).join(' · ')}</dd></div>
      <div><dt className="text-ink-soft">Enquadramento na REN 846</dt>
        {t.grupo_mais_grave ? <><dd className="mt-1 font-semibold">{t.grupos.map(rotuloDoGrupo).join(', ')} <AjudaGrupos p={plano} /> · {t.infracoes.join('; ')}</dd><dd className="mt-1 text-xs text-ink-soft">Identificado pelo texto em {t.na_fila} de {t.n}; {t.a_confirmar} a confirmar.</dd></>
          : <dd className="mt-1 font-semibold">A confirmar</dd>}
        {t.ia && <dd className="mt-2 text-xs"><Tag kind="ai" /> <span className="text-ink-soft">sugere {t.ia.dispositivo} em {t.ia.n} de {t.ia.de}. Aguarda revisão humana; entra só no cenário preliminar, marcada.</span></dd>}</div>
      <div><dt className="text-ink-soft">Como provar que cumpriu <Tag kind="review" label="Sugestão" /></dt>
        {t.evidencias.length ? <dd><ul className="mt-1 list-disc space-y-1 pl-4">{t.evidencias.map((x) => <li key={x.id}>{plano.evidencias[x.id]} <span className="text-xs text-ink-soft">({x.n})</span></li>)}</ul></dd> : <dd className="mt-1">Definir com a equipe responsável.</dd>}</div>
    </dl>
    <div className="mt-5"><h4 className="text-sm font-semibold">Obrigações principais</h4>
      <ul className="mt-2 space-y-2">{t.principais.map((id) => { const o = obrigacao(id); return <li key={id} className="flex flex-wrap items-baseline gap-x-3 gap-y-1"><Titulo o={o} /><span className="text-xs text-ink-soft">{o.prazo.texto}</span></li> })}</ul></div>

    <AnalisePreliminar t={t} />

    <details className="mt-4 print:hidden">
      <summary className={SUMARIO}>Ver as {t.n} obrigações e o porquê<Chevron /></summary>
      {e && <Atenuantes e={e} />}
      <p className="mt-3 text-xs text-ink-soft">Valor provável: sem histórico de multas para este tema.</p>
      <ul className="mt-4 space-y-3">{t.obrigacoes.map((id) => <ItemObrigacao key={id} o={obrigacao(id)} />)}</ul>
    </details>
    {t.fontes.length > 0 && <p className="mt-4 text-xs text-ink-soft">Tema pela norma: {t.fontes.map((f) => `${f.rotulo}, “${f.titulo}”`).join('; ')}.</p>}
  </li>
}

/** Do teto ao art. 24, II e ao art. 24, I, com os valores escritos. A barra é relativa ao maior valor entre os temas. */
function Escada({ e, maiorPct }: { e: Exposicao; maiorPct: number }) {
  const { sim } = useContext(Cenario)
  const s = sim ?? SIM_INICIAL
  const passo = (rotulo: string, p: number | null) => p == null ? null : { rotulo, p }
  const passos = [
    passo('teto do grupo', e.pct),
    ATEN_II ? passo(ATEN_II.dispositivo.replace('Art.', 'art.'), comAtenuantePct(e.faixa, s, 'ate_tn')) : null,
    ATEN_I ? passo(ATEN_I.dispositivo.replace('Art.', 'art.'), comAtenuantePct(e.faixa, s, 'espontanea')) : null,
  ].filter((x): x is { rotulo: string; p: number } => x != null)
  const menor = ATEN_I ? comAtenuantePct(e.faixa, s, 'espontanea') : null
  return <>
    {menor != null && <p className="mt-1 text-sm">pode cair para <strong>{emReais(menor, sim)}</strong> se regularizar antes da fiscalização ({ATEN_I!.dispositivo.replace('Art.', 'art.')})</p>}
    <ul className="mt-3 space-y-1.5" aria-label="Do teto aos atenuantes do art. 24">
      {passos.map((x) => <li key={x.rotulo} className="grid grid-cols-[6.5rem_1fr_auto] items-center gap-2 text-xs sm:grid-cols-[8rem_1fr_auto]">
        <span className="text-ink-soft">{x.rotulo}</span>
        <span aria-hidden="true" className="h-3 overflow-hidden bg-stone print:border print:border-line">
          <span className={`block h-full ${e.origem === 'sugerido' ? 'hachura' : 'bg-slate-blue'}`} style={{ width: `${maiorPct ? Math.max(2, (x.p / maiorPct) * 100) : 0}%` }} />
        </span>
        <span className="tabular-nums font-medium text-obsidian">{emReais(x.p, sim)}</span>
      </li>)}
    </ul>
  </>
}

/** Atenuantes do art. 24 sobre a faixa do tema (só no detalhe, nunca na manchete). */
function Atenuantes({ e }: { e: Exposicao }) {
  const { sim } = useContext(Cenario)
  const s = sim ?? SIM_INICIAL
  const itens = ATENUANTES.map((m) => [m, comAtenuantePct(e.faixa, s, m.cenario!)] as const).filter(([, v]) => v != null)
  if (!itens.length) return null
  return <p className="mt-3 text-sm">Com atenuante do {itens.map(([m, v], i) => <span key={m.parametro}>{i ? '; ' : ''}<LinkFonte sha256={m.sha256} trecho={m.trecho}>{m.dispositivo}</LinkFonte>: até <strong>{emReais(v!, sim)}</strong></span>)}. Vale um atenuante só; pior caso, sem agravantes{e.origem === 'sugerido' ? `; ${PRELIMINAR}` : ''}.</p>
}

function Titulo({ o }: { o: Obrigacao }) {
  return <span className="font-medium [overflow-wrap:anywhere]">{o.titulo_completo}{o.titulo_origem === 'ia' && <Sparkles role="img" aria-label="título resumido com IA, a revisar" className="ml-1 inline h-3 w-3 text-slate-blue" />}</span>
}

function ItemObrigacao({ o }: { o: Obrigacao }) {
  const [aberto, setAberto] = useState(false)
  return <li id={idDaObrigacao(o.id)} className="rounded-xl border border-line"><details className="p-4" onToggle={(e) => setAberto(e.currentTarget.open)}>
    <summary className="-m-2 flex min-h-11 cursor-pointer items-center gap-3 rounded-lg p-2 hover:bg-slate-blue/5"><span className="min-w-0"><Titulo o={o} /><span className="ml-2 text-xs text-ink-soft">{o.prazo.texto}{o.dispositivo ? ` · ${o.dispositivo}` : ''}</span></span><Chevron /></summary>
    {aberto && <PorQue o={o} />}
  </details></li>
}

function PorQue({ o }: { o: Obrigacao }) {
  const rascunhos = rascunhosDoItem(plano.rascunhos_aneel, o.id)
  return <div className="mt-4 space-y-4 text-sm leading-relaxed">
      <ComparacaoAnterior o={o} />
      <div><h5 className="font-semibold">O que a norma diz <Tag kind="source" /></h5>
        {o.sujeito_implicito && <p className="mt-1 text-xs font-semibold">Sujeito implícito (a revisar): o texto não diz “a distribuidora”; contamos como dever dela por ser norma dirigida às distribuidoras.</p>}
        {o.trecho ? <><blockquote className="mt-2 border-l-2 border-bronze bg-ivory p-3">“{o.trecho}”</blockquote><p className="mt-1 text-xs text-ink-soft"><LinkFonte sha256={plano.norma.sha256} trecho={o.trecho}>{o.dispositivo}</LinkFonte> · trecho literal conferido na fonte · <LinkFonte sha256={plano.norma.sha256} trecho={o.trecho}>{plano.norma.titulo}</LinkFonte></p></>
          : <p className="mt-1">Sem citação verificada: confira o dispositivo na fonte. {o.motivo_sem_calculo}</p>}</div>
      <div><h5 className="font-semibold">Infração da REN 846</h5>
        {o.enquadramento.map((e) => <blockquote key={e.dispositivo} className="mt-2 border-l-2 border-slate-blue bg-ivory p-3"><strong><LinkFonte sha256={plano.infracoes[e.dispositivo].fonte.sha256} trecho={plano.infracoes[e.dispositivo].trecho}>{e.dispositivo}</LinkFonte> · {rotuloDoGrupo(e.grupo)}</strong> <AjudaGrupos p={plano} /> <span className="text-xs text-ink-soft">(o texto da obrigação nomeia o instrumento desta infração)</span><ProvInfracao d={e.dispositivo} /><p>“{plano.infracoes[e.dispositivo].trecho}”</p></blockquote>)}
        {!o.enquadramento.length && o.ia && <div className="mt-2 rounded-lg border border-dashed border-slate-blue/40 p-3">
          <p className="flex flex-wrap gap-2"><Tag kind="ai" /><Tag kind="review" /></p>
          <p className="mt-2"><strong><LinkFonte sha256={plano.infracoes[o.ia.dispositivo].fonte.sha256} trecho={plano.infracoes[o.ia.dispositivo].trecho}>{o.ia.dispositivo}</LinkFonte> · {rotuloDoGrupo(o.ia.grupo)}</strong> <AjudaGrupos p={plano} />: “{plano.infracoes[o.ia.dispositivo].trecho}”</p><ProvInfracao d={o.ia.dispositivo} />
          <p className="mt-1 text-ink-soft">{o.ia.justificativa}</p>
          {o.ia.duvida && <SucessaoNoTempo dispositivo={o.ia.dispositivo} />}
          <p className="mt-1 text-xs">Entra só no cenário preliminar, marcada como sugerida, até uma pessoa confirmar.</p></div>}
        {!o.enquadramento.length && !o.ia && <p className="mt-1">Enquadramento a confirmar.</p>}</div>
      <div><h5 className="font-semibold">Prazo</h5><p>{o.prazo.texto}{o.prazo.provisorio ? '. Data provisória: calculada a partir da publicação da norma, aguarda confirmação da contagem por uma pessoa.' : '.'}</p>
        {o.marco?.trecho && <blockquote className="mt-2 border-l-2 border-bronze bg-ivory p-3"><strong><LinkFonte sha256={plano.norma.sha256} trecho={o.marco.trecho}>{o.marco.dispositivo}</LinkFonte></strong> · “{o.marco.trecho}”</blockquote>}</div>
      {o.premissas.length > 0 && <div><h5 className="font-semibold">Premissas da faixa</h5><ul className="list-disc space-y-1 pl-5">{o.premissas.map((p) => <li key={p}>{p}</li>)}</ul></div>}
      {o.evidencias.length > 0 && <div><h5 className="font-semibold">Como provar <Tag kind="review" label="Sugestão" /></h5><ul className="list-disc space-y-1 pl-5">{o.evidencias.map((e) => <li key={e.id}>{plano.evidencias[e.id]}: <span className="text-ink-soft">“…{e.trecho}…”</span></li>)}</ul></div>}
      {rascunhos.length > 0 && <details className="border border-line p-3"><summary className="cursor-pointer font-semibold">Rascunho de pergunta à ANEEL ({rascunhos.length})</summary><div className="mt-3"><RascunhosAneel rascunhos={rascunhos} /></div></details>}
      <p className="text-xs text-ink-soft">Tema: {o.motivo_tema}.</p>
    </div>
}

const SELO_ANALISE = plano.analise.rotulo.includes('revisar com o jurídico') ? plano.analise.rotulo : `${plano.analise.rotulo} · revisar com o jurídico`

/** Análise regulatória preliminar do tema: recolhida; o conteúdo só é montado ao abrir (ou na impressão). */
function AnalisePreliminar({ t }: { t: Tema }) {
  const [aberto, setAberto] = useState(false)
  return <details className="mt-5 rounded-xl border border-slate-blue/30 bg-ivory open:border-line" onToggle={(e) => setAberto(e.currentTarget.open)}>
    <summary className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl px-4 py-2 font-semibold text-slate-blue hover:bg-slate-blue/5"><span className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">Análise regulatória preliminar <span className="text-xs font-normal text-ink-soft">tipo de obrigação, como cumprir, o que provar</span></span><Chevron /></summary>
    {aberto && <ConteudoAnalise t={t} />}
  </details>
}

function DependenciaAto({ itens }: { itens: { obrigacao?: string; id: string; trecho_literal: string }[] }) {
  const ato = itens.filter((d) => d.id === 'ato_da_aneel')
  const outros = itens.filter((d) => d.id !== 'ato_da_aneel')
  const bloco = (titulo: string, lista: typeof itens) => lista.length > 0 && <div className="rounded-lg border border-pending/50 bg-stone p-3">
    <p className="flex items-start gap-2 font-semibold text-obsidian"><AlertTriangle aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-pending" />{titulo}</p>
    {lista.map((d) => <figure key={`${d.obrigacao ?? ''}${d.trecho_literal}`} className="mt-2">
      <blockquote className="border-l-2 border-bronze bg-white p-2 text-sm">“{d.trecho_literal}”</blockquote>
      <figcaption className="mt-1 text-xs text-ink-soft">{d.obrigacao ? `${obrigacao(d.obrigacao).dispositivo ?? 'dispositivo a confirmar'} · ` : ''}trecho literal conferido na fonte</figcaption>
    </figure>)}
  </div>
  return <>
    {bloco('Prazo condicionado a ato da ANEEL: verificar se as instruções foram publicadas', ato)}
    {outros.length > 0 && bloco(`Cumprimento depende de terceiro: ${plano.analise.dependencias[outros[0].id]?.nome ?? 'a avaliar'}`, outros)}
  </>
}

function ConteudoAnalise({ t }: { t: Tema }) {
  const a = plano.analise
  const pratica = a.pratica_por_tema[t.id] ? a.dependencias[a.pratica_por_tema[t.id]] : undefined
  return <div className="space-y-5 px-4 pb-4 text-sm leading-relaxed">
    <p className="inline-block rounded-md border border-pending/50 bg-stone px-2.5 py-1 text-xs font-semibold text-pending">{SELO_ANALISE}</p>
    {t.dependencias_no_texto.length > 0 && <DependenciaAto itens={t.dependencias_no_texto} />}
    {t.principais.map((id) => <AnaliseObrigacao key={id} o={obrigacao(id)} />)}
    {pratica && <div className="rounded-lg border border-dashed border-line p-3 text-xs">
      <h5 className="text-sm font-semibold">Prática conhecida (fora do texto da norma) <Tag kind="review" label="Sugestão" /></h5>
      <p className="mt-1 font-medium">{pratica.nome}</p>
      <p className="mt-1 text-ink-soft">{pratica.cautela}</p>
      <p className="mt-2"><strong>Caminho:</strong> {pratica.caminho}</p>
      <p className="mt-2 font-semibold">O que guardar desde já</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-4">{pratica.o_que_guardar.map((g) => <li key={g}>{g}</li>)}</ul>
      <p className="mt-2 font-semibold">Referências públicas</p>
      <ul className="mt-1 space-y-1">
        {pratica.precedentes.filter((p) => p.titulo !== a.contraponto.titulo).map((p) => <Referencia key={p.id} titulo={p.titulo} urls={p.urls} nota={p.a_confirmar} />)}
        <Referencia titulo={a.contraponto.titulo} urls={a.contraponto.urls} nota={a.contraponto.a_confirmar} rotulo="Contraponto" />
      </ul>
    </div>}
  </div>
}

function Referencia({ titulo, urls, nota, rotulo }: { titulo: string; urls: string[]; nota: string; rotulo?: string }) {
  const host = (u: string) => { try { return new URL(u).hostname.replace(/^www\./, '') } catch { return u } }
  return <li>{rotulo && <strong>{rotulo}: </strong>}{titulo}{' '}
    {urls.map((u, i) => <span key={u}>{i ? ', ' : '('}<a className="break-all text-slate-blue underline" href={u} rel="noopener noreferrer" target="_blank">{host(u)}</a>{i === urls.length - 1 ? ')' : ''}</span>)}
    <span className="block text-ink-soft">{nota}</span></li>
}

function AnaliseObrigacao({ o }: { o: Obrigacao }) {
  const an = o.analise
  const tipo = an?.tipo
  const manual = tipo && tipo.id && (tipo.situacao === 'concordam' || tipo.situacao === 'so_regra') ? plano.analise.manuais[tipo.id] : undefined
  const nomeTipo = !tipo ? 'tipo a revisar'
    : tipo.situacao === 'concordam' ? tipo.nome
      : tipo.situacao === 'so_regra' ? `${tipo.nome} · só pela regra, segunda leitura da IA não feita (a revisar)`
        : tipo.situacao === 'a_revisar' ? 'tipo a revisar' : 'sem tipo próprio'
  return <article className="border-t border-line pt-4">
    <h5 className="font-semibold"><Titulo o={o} /> <span className="text-xs font-normal text-ink-soft">· <LinkFonte sha256={plano.norma.sha256} trecho={o.trecho}>{o.dispositivo ?? 'dispositivo a confirmar'}</LinkFonte></span></h5>
    <p className="mt-2 text-xs font-semibold text-ink-soft ">O que a norma exige <Tag kind="source" /></p>
    {o.trecho ? <><blockquote className="mt-1 border-l-2 border-bronze bg-white p-3">“{o.trecho}”</blockquote><p className="mt-1 text-xs text-ink-soft"><LinkFonte sha256={plano.norma.sha256} trecho={o.trecho}>{o.dispositivo}</LinkFonte> · trecho literal conferido na fonte</p></>
      : <p className="mt-1">Sem citação verificada: confira o dispositivo na fonte.</p>}
    {an && an.dependencias_no_texto.some((d) => d.id === 'ato_da_aneel') && <p className="mt-2 flex items-start gap-2 text-xs font-semibold text-pending"><AlertTriangle aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0" />Prazo condicionado a ato da ANEEL: verificar se as instruções foram publicadas.</p>}
    <p className="mt-3"><span className="text-ink-soft">Tipo:</span> {nomeTipo}</p>
    {manual && <div className="mt-3 grid gap-4 sm:grid-cols-2">
      <div><p className="font-semibold">Como cumprir <Tag kind="review" label="Sugestão" /></p><ul className="mt-1 list-disc space-y-1 pl-4">{manual.ideias_cumprimento.map((x) => <li key={x}>{x}</li>)}</ul></div>
      <div><p className="font-semibold">O que provar para a ANEEL <Tag kind="review" label="Sugestão" /></p><ul className="mt-1 list-disc space-y-1 pl-4">{manual.evidencias.map((x) => <li key={x}>{x}</li>)}</ul></div>
    </div>}
  </article>
}

function LinhaDoTempo() {
  const colunas: { titulo: string; ids: string[]; vazio: string }[] = [
    { titulo: 'Vencidas', ids: plano.linha_do_tempo.vencida, vazio: 'Nenhuma.' },
    { titulo: 'Próximos 90 dias', ids: plano.linha_do_tempo['90dias'], vazio: 'Nenhuma obrigação vence nos próximos 90 dias.' },
    { titulo: 'Recorrentes', ids: plano.linha_do_tempo.recorrente, vazio: 'Nenhuma.' },
  ]
  const nomeTema = new Map(plano.temas.map((t) => [t.id, t.nome]))
  const semData = [...plano.linha_do_tempo.evento, ...plano.linha_do_tempo.sem_prazo]
  const porTema = plano.temas.map((t) => [t.nome, semData.filter((id) => obrigacao(id).tema === t.id).length] as const).filter(([, n]) => n)
  return <div>
    <p className="max-w-3xl text-sm text-ink-soft">Datas calculadas a partir do texto, a confirmar. {plano.linha_do_tempo.depois.length > 0 && `${plano.linha_do_tempo.depois.length} vencem depois de 90 dias.`}</p>
    <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {colunas.map((c) => <div key={c.titulo} className="rounded-2xl border border-line bg-white p-5">
        <h3 className="font-semibold">{c.titulo} <span className="text-ink-soft">({c.ids.length})</span></h3>
        {c.ids.length ? <ul className="mt-3 space-y-3 text-sm">{c.ids.map((id) => { const o = obrigacao(id); return <li key={id}><Titulo o={o} /><p className="text-xs text-ink-soft">{o.prazo.texto} · {nomeTema.get(o.tema)}</p></li> })}</ul> : <p className="mt-3 text-sm text-ink-soft">{c.vazio}</p>}
      </div>)}
      <div className="rounded-2xl border border-line bg-white p-5">
        <h3 className="font-semibold">Sem data <span className="text-ink-soft">({semData.length})</span></h3>
        <p className="mt-1 text-xs text-ink-soft">{plano.linha_do_tempo.evento.length} dependem de um evento ainda sem data; {plano.linha_do_tempo.sem_prazo.length} não têm prazo no texto.</p>
        <ul className="mt-3 space-y-1 text-sm">{porTema.map(([nome, n]) => <li key={nome} className="flex justify-between gap-3"><span>{nome}</span><span className="text-ink-soft">{n}</span></li>)}</ul>
      </div>
    </div>
  </div>
}

const emReais = (v: number, s: Simulacao | null) => (s ? brl(reaisDe(v, s)) : `${pct(v)} da receita`)

function Citado({ c }: { c: Citacao }) {
  return <div className="mt-2">
    <blockquote className="border-l-2 border-bronze bg-ivory p-3 text-sm">“{c.trecho}”</blockquote>
    <p className="mt-1 break-all text-xs text-ink-soft"><LinkFonte sha256={c.sha256} trecho={c.trecho}>{c.dispositivo}</LinkFonte> · {c.fonte} · SHA-256 {c.sha256}</p>
  </div>
}

function Interpretacao({ children }: { children: ReactNode }) {
  return <div className="mt-3 rounded-lg border border-dashed border-slate-blue/40 p-3 text-sm"><Tag kind="review" label="Interpretação · aguarda revisão humana" /><div className="mt-2 space-y-1">{children}</div></div>
}

function ComoReduzir({ temas }: { temas: Tema[] }) {
  const red = plano.reducao
  return <div>
    <p className="inline-block border border-bronze/50 bg-stone/60 px-3 py-1 text-xs font-semibold">{red.rotulo}</p>
    <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-soft">O que a REN 846 prevê para reduzir ou trocar a multa. Cada medida traz o texto da norma e, separada em caixa tracejada, a nossa leitura da condição e do efeito.</p>
    <div className="mt-6 grid gap-4 lg:grid-cols-2">{red.medidas.map((m) => <CartaoMedida key={m.parametro} m={m} />)}</div>
    <details className="mt-4">
      <summary className={SUMARIO}><span className="min-w-0">Regras que valem para todos os atenuantes ({red.regras.map((c) => c.dispositivo).join('; ')})</span><Chevron /></summary>
      <div className="mt-3 space-y-3">{red.regras.map((c) => <Citado key={c.parametro} c={c} />)}</div>
      <Interpretacao><p>Os atenuantes não se somam: vale um só. E só contam se a cessação e a reparação forem comprovadas à Fiscalização antes do Auto de Infração. Por isso a prova datada precisa existir desde já.</p></Interpretacao>
    </details>
    <h3 className="font-display mt-10 text-2xl">Por tema</h3>
    <p className="mt-2 max-w-3xl text-sm text-ink-soft">Valores com a receita escolhida no topo, por infração. Pior caso: valor base no teto do grupo, sem agravantes; cada cenário usa um único atenuante.</p>
    <ol className="mt-4 space-y-4">{temas.map((t) => <ReducaoTema key={t.id} t={t} />)}</ol>
  </div>
}

function CartaoMedida({ m }: { m: Medida }) {
  return <article className="rounded-2xl border border-line bg-white p-5">
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <h3 className="font-semibold leading-snug">{m.nome}</h3>
      <span className={`px-2.5 py-0.5 text-xs font-semibold ${m.percentual != null ? 'bg-slate-blue text-ivory' : 'bg-stone text-ink-soft'}`}>{m.percentual != null ? `−${pct(m.percentual)}` : 'o texto não fixa percentual'}</span>
    </div>
    <p className="mt-2"><Tag kind="source" /></p>
    <Citado c={m} />
    <Interpretacao><p><strong>Condição:</strong> {m.condicao}</p><p><strong>Efeito:</strong> {m.efeito}</p></Interpretacao>
  </article>
}

/** Causa externa concreta do tema: no texto (com citação), prática conhecida (fora do texto) ou nenhuma. */
function CausasExternas({ t }: { t: Tema }) {
  const a = plano.analise
  const dep = a.pratica_por_tema[t.id] ? a.dependencias[a.pratica_por_tema[t.id]] : undefined
  const outra = a.causas_por_tema[t.id]
  const texto = t.dependencias_no_texto
  if (!texto.length && !t.excludentes.length && !dep && !outra) return <dd className="mt-1 font-semibold">nenhuma identificada</dd>
  return <dd className="space-y-3">
    {texto.map((d) => <div key={d.obrigacao} className="mt-1">
      <p className="font-semibold">Instruções da ANEEL ainda por publicar <span className="text-xs font-normal text-ink-soft">(no texto, com citação)</span></p>
      <blockquote className="mt-1 border-l-2 border-bronze bg-ivory p-3 text-xs">“{d.trecho_literal}” <span className="block text-ink-soft">{obrigacao(d.obrigacao).dispositivo} · {plano.norma.titulo}</span></blockquote>
    </div>)}
    {t.excludentes.map((x) => <blockquote key={x.obrigacao} className="mt-1 border-l-2 border-bronze bg-ivory p-3 text-xs">“{x.trecho}” <span className="block text-ink-soft">{obrigacao(x.obrigacao).dispositivo} · {plano.norma.titulo}</span></blockquote>)}
    {dep && <p className="mt-1"><span className="font-semibold">{dep.nome}</span> <span className="text-xs text-ink-soft">(prática conhecida, fora do texto da norma; veja a análise preliminar)</span></p>}
    {outra && <p className="mt-1"><span className="font-semibold">{outra.nome}</span> <span className="block text-xs text-ink-soft">{outra.nota}</span></p>}
  </dd>
}

function ReducaoTema({ t }: { t: Tema }) {
  const { sim, modo } = useContext(Cenario)
  const s = sim ?? SIM_INICIAL
  const e = exposicaoTema(t, sim, modo)
  const f = e?.faixa
  return <li className="rounded-2xl border border-line bg-white p-5 sm:p-6">
    <h4 className="font-display text-xl leading-tight">{t.nome} <span className="text-sm text-ink-soft">· {t.n} {t.n === 1 ? 'obrigação' : 'obrigações'}</span></h4>
    <dl className="mt-4 grid gap-5 text-sm md:grid-cols-3">
      <div><dt className="flex flex-wrap items-center gap-1 text-ink-soft">Exposição por infração <Tag kind="estimate" />{e?.origem === 'sugerido' && <Sugerido />}</dt>
        {e && f ? <dd><ul className="mt-1 space-y-1">
          <li>Sem atenuante: até <strong>{valor(e)}</strong></li>
          {ATENUANTES.map((m) => { const v = comAtenuantePct(f, s, m.cenario!); return v == null ? null : <li key={m.parametro}>{m.dispositivo} (−{pct(m.percentual!)}): até <strong>{emReais(v, sim)}</strong></li> })}
        </ul><p className="mt-1 text-xs text-ink-soft">{rotuloDoGrupo(maisGrave(e.origem === 'confirmado' ? t.grupos : t.grupos_sugeridos))} <AjudaGrupos p={plano} />{e.origem === 'sugerido' ? ` (${PRELIMINAR})` : ''}. Também pode caber advertência (art. 6º).</p></dd>
          : <dd className="mt-1">Exposição a enquadrar. Se houver multa, os atenuantes do art. 24 reduzem o valor calculado em {ATENUANTES.map((m) => pct(m.percentual!)).join(' ou ')}, conforme a condição.</dd>}
      </div>
      <div><dt className="text-ink-soft">Causas externas</dt><CausasExternas t={t} /></div>
      <div><dt className="text-ink-soft">O que guardar desde já <Tag kind="review" label="Sugestão" /></dt>
        {t.guardar.length ? <dd><ul className="mt-1 list-disc space-y-1 pl-4">{t.guardar.map((g) => <li key={g.id}>{plano.guardar[g.id]} <span className="text-xs text-ink-soft">({g.n} {g.n === 1 ? 'obrigação' : 'obrigações'})</span></li>)}</ul></dd>
          : <dd className="mt-1">Definir com a equipe responsável.</dd>}
        <dd className="mt-1 text-xs text-ink-soft">Boa prática, não exigência da norma.</dd>
      </div>
    </dl>
  </li>
}
