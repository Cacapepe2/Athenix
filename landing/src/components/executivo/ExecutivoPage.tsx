import { LinkFonte } from '../ui/LinkFonte'
import { useEffect, useRef, useState } from 'react'
import { NORMA_PADRAO, NORMAS, norma as dadosDa, prazos, queda, textoContagem, top5, urlPlanoCompleto, urlRelatorio, valorGeral, type LinhaTop5 } from '../../content/executivo'
import { RespostasProvider, useRespostas } from '../plano/Respostas'
import { prontidao } from '../../content/prontidao'
import { useHoje } from '../../hooks/useHoje'
import { brlCurto, dataBR, normaDaUrl, textoVencidasComDetalhe, type NormaId, type Simulacao } from '../../content/plano'

// Visão executiva (/demo/executivo): três números e até cinco blocos clicáveis. Muito pouco texto; o resto
// fica no plano completo. Todos os números vêm de content/executivo.ts (planos gerados pelo motor).
const MODO = 'preliminar' as const
const PORTE_PADRAO = 'media'
const LINK = 'font-semibold underline underline-offset-4 hover:text-acento'
const GRANDE = 'block text-[64px] leading-[0.95] font-bold sm:text-[80px] lg:text-[96px]'
const GRANDE_4 = 'block text-[56px] leading-[0.95] font-bold sm:text-[64px] lg:text-[72px]' // com o 4º número a linha tem 4 colunas
const LEGENDA = 'text-[17px] font-semibold'

const valorDoBloco = (l: LinhaTop5) => (l.valor?.reais != null ? `${brlCurto(l.valor.reais)}${l.preliminar ? '*' : ''}` : 'a enquadrar')

export function ExecutivoPage() {
  const [normaId, setNormaId] = useState<NormaId>(normaDaUrl)
  return <RespostasProvider norma={normaId}><Executiva normaId={normaId} setNormaId={setNormaId} /></RespostasProvider>
}

function Executiva({ normaId, setNormaId }: { normaId: NormaId; setNormaId: (id: NormaId) => void }) {
  const { respostas } = useRespostas()
  const [porteId, setPorteId] = useState(PORTE_PADRAO)
  const [aberto, setAberto] = useState<string | null>(null)
  const [ultimo, setUltimo] = useState<string | null>(null) // o painel, ao fechar, mantém o último conteúdo
  const n = dadosDa(normaId)
  const p = n.dados
  const faixa = p.simulador.faixas.find((f) => f.id === porteId) ?? p.simulador.faixas[1]
  const sim: Simulacao = { base: faixa.base, faturamento: null }
  const v = valorGeral(p, sim, MODO)
  const q = queda(p, sim, MODO)
  // Datas só depois da montagem (useHoje): o HTML pré-renderizado no build não pode trazer "hoje". Até lá, os
  // cinco blocos seguem a data de geração do plano (igual no servidor e no cliente) e prazos ficam neutros.
  const hoje = useHoje()
  const pz = hoje ? prazos(p, hoje) : null
  const linhas = top5(normaId, sim, MODO, 5, hoje ?? p.gerado_em)
  const sel = linhas.find((l) => l.id === ultimo) ?? null
  const painelRef = useRef<HTMLDivElement>(null)
  const blocos = useRef<Record<string, HTMLButtonElement | null>>({})
  // Ao abrir, traz o painel para a tela (no celular ele fica abaixo dos cinco blocos).
  useEffect(() => {
    if (aberto) painelRef.current?.scrollIntoView({ block: 'nearest', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
  }, [aberto])
  const preliminar = v?.origem === 'sugerido'
  const pr = prontidao(p, respostas, sim, MODO) // o quarto número só aparece depois de marcar provas no plano
  const grande = pr.algumaMarcada ? GRANDE_4 : GRANDE

  const trocarNorma = (id: NormaId) => {
    setNormaId(id)
    setAberto(null)
    setUltimo(null)
    const q = new URLSearchParams(location.search)
    if (id === NORMA_PADRAO) q.delete('norma')
    else q.set('norma', id)
    history.replaceState(history.state, '', `${location.pathname}${q.size ? `?${q}` : ''}${location.hash}`)
  }
  const alternar = (id: string) => {
    setAberto(aberto === id ? null : id)
    setUltimo(id)
  }

  return <main id="executivo" className="mx-auto flex max-w-[1200px] flex-col gap-10 px-4 pt-6 pb-12 sm:px-8">
    <header className="flex flex-wrap items-center justify-between gap-4 border-b-[length:var(--borda-titulo)] border-obsidian pb-4">
      <a href="/" aria-label="Athenix, voltar ao início" className="text-[28px] font-bold ">Athenix</a>
      <div className="flex flex-wrap items-center gap-3.5">
        <div role="group" aria-label="Norma" className="flex">
          {NORMAS.map((x) => <button key={x.id} type="button" className="seg" aria-pressed={normaId === x.id} onClick={() => trocarNorma(x.id)}>{x.rotulo.replace('/2025', '').replace('/2026', '')}</button>)}
        </div>
        <div role="group" aria-label="Porte da distribuidora (receita operacional líquida anual)" className="flex">
          {p.simulador.faixas.map((x) => <button key={x.id} type="button" className="seg" aria-pressed={faixa.id === x.id} onClick={() => setPorteId(x.id)}>R$ {x.base / 1e9} bi</button>)}
        </div>
      </div>
      <a href={urlPlanoCompleto(normaId)} className={`text-[15px] ${LINK}`}>Plano completo →</a>
    </header>

    <section aria-label="Resumo" aria-live="polite" className="grid gap-8 [grid-template-columns:repeat(auto-fit,minmax(260px,1fr))]">
      <div className="flex flex-col gap-1.5">
        <span className={`${grande} text-acento`}>{v?.reais != null ? <><span className="mr-2 text-[0.4em] align-baseline">R$</span>{brlCurto(v.reais).replace('R$ ', '')}</> : 'a enquadrar'}</span>
        <span className={LEGENDA}>por infração{preliminar ? '*' : ''}</span>
      </div>
      <div className="flex flex-col gap-1.5">
        <span className={grande}>{q ? `−${Math.round(q.reducaoPct)}%` : '—'}</span>
        <span className={LEGENDA}>se agir antes da fiscalização</span>
      </div>
      <div className="flex flex-col gap-1.5">
        {!pz
          ? <><span className={grande} aria-hidden="true">—</span><span className={LEGENDA}>prazos contados com a data de hoje</span></>
          : pz.vencidas > 0
          ? <><span className={grande}>{pz.vencidas}</span><span className={LEGENDA}>{textoVencidasComDetalhe({ obrigacoes: pz.vencidas, detalhes: pz.detalhes }).replace(/^\d+ /, '')}</span></>
          : pz.proximoMarco
            ? <><span className="block text-[length:var(--tamanho-data-executiva)] leading-[0.95] font-bold">{dataBR(pz.proximoMarco.data)}</span><span className={LEGENDA}>próximo marco · {pz.proximoMarco.tipo}</span></>
            : pz.proxima
              ? <><span className={grande}>{pz.proxima.dias} dias</span><span className={LEGENDA}>até o próximo prazo</span></>
              : <><span className={grande}>—</span><span className={LEGENDA}>nenhum prazo a vencer</span></>}
        {pz?.contagem && <span className="text-xs">{textoContagem(pz.contagem)}</span>}
      </div>
      {pr.algumaMarcada && <div className="flex flex-col gap-1.5"><span className={grande}>{pr.geral.x} de {pr.geral.y}</span><span className={LEGENDA}>provas em mãos · checklist sugerido</span></div>}
    </section>

    <section aria-labelledby="comece-por" className="flex flex-col gap-3.5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="comece-por" className="text-[17px] font-bold">Comece por</h2>
        <span className="text-sm">Toque num item para ver o que fazer</span>
      </div>
      <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(190px,1fr))]">
        {linhas.map((l) => {
          const aberta = aberto === l.id
          const vencida = hoje != null && l.situacao === 'vencida'
          return <button key={l.id} ref={(el) => { blocos.current[l.id] = el }} type="button" className="bloco flex min-h-[196px] flex-col gap-2.5 p-4 text-left" aria-expanded={aberta} aria-controls="painel" onClick={() => alternar(l.id)}>
            <span className={`inline-flex items-center gap-1.5 text-xs font-bold ${vencida && !aberta ? 'text-bronze-deep' : ''}`}>
              <span aria-hidden="true" className={`inline-block h-2 w-2 rounded-full ${vencida ? 'bg-acento' : aberta ? 'bg-white' : 'bg-obsidian'}`} />{hoje ? l.prazoCurto : 'prazo contado com a data de hoje'}
            </span>
            <span className="text-base leading-tight font-semibold">{l.titulo}</span>
            <span className="mt-auto text-[30px] font-bold ">{valorDoBloco(l)}</span>
            <span className="flex items-center justify-between border-t border-current pt-2.5 text-[13px] font-semibold">
              <span>{aberta ? 'Fechar' : 'Ver o que fazer'}</span><span aria-hidden="true" className="seta text-lg">{aberta ? '↑' : '↓'}</span>
            </span>
          </button>
        })}
      </div>

      <div id="painel" ref={painelRef} role="region" aria-label="Detalhes da obrigação" className="painel" data-aberto={aberto ? 'true' : 'false'}>
        <div className="painel-miolo" inert={!aberto}>
          {sel && <Painel l={sel} fechar={() => { setAberto(null); blocos.current[sel.id]?.focus() }} />}
        </div>
      </div>
    </section>

    <footer className="flex flex-wrap justify-between gap-3 border-t border-obsidian pt-3.5 text-[13px]">
      <span>* preliminar · valores ilustrativos · não é parecer jurídico · dias contados até {hoje ? dataBR(hoje) : 'hoje'}</span>
      <span className="flex gap-4"><a href={urlRelatorio(normaId)} className="font-semibold">Baixar meu relatório</a><a href={urlPlanoCompleto(normaId)} className="font-semibold">Plano completo →</a></span>
    </footer>
  </main>
}

const COLUNA = 'flex flex-col gap-2 border-r border-line px-6 py-5 last:border-r-0'
const TITULO_COLUNA = 'text-[13px] font-bold'

function Painel({ l, fechar }: { l: LinhaTop5; fechar: () => void }) {
  const p = dadosDa(l.normaId).dados
  return <div className="painel-in">
    <div className="flex flex-wrap items-start justify-between gap-4 border-b-[length:var(--borda-forte)] border-obsidian px-6 py-5">
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="text-[13px] font-semibold"><LinkFonte sha256={dadosDa(l.normaId).dados.norma.sha256} trecho={l.trecho}>{l.dispositivo ?? 'dispositivo a confirmar'}</LinkFonte></span>
        <span className="text-[22px] leading-tight font-bold">{l.frase}</span>
        <span className="text-xs">Título do bloco: resumo gerado por IA, a revisar.</span>
      </div>
      <button type="button" onClick={fechar} aria-label="Fechar detalhes" className="seg">Fechar ✕</button>
    </div>
    <div className="grid [grid-template-columns:repeat(auto-fit,minmax(220px,1fr))]">
      <div className={COLUNA}>
        <span className={TITULO_COLUNA}>Prazo</span>
        <span className="text-lg font-bold">{l.prazoCurto}</span>
        {l.prazoBase && <span className="text-[13px]">{l.prazoBase}</span>}
      </div>
      <div className={COLUNA}>
        <span className={TITULO_COLUNA}>Gravidade e valor por infração</span>
        <span className="text-[15px]">{l.valor ? `${l.gravidadeRotulo} · ${l.preliminar ? 'sugerida pela IA, aguarda revisão humana' : 'identificada no texto'}` : 'gravidade a enquadrar'}</span>
        {l.barras.length > 0 && <span className="text-xs">Atenuantes do art. 24: valem se a infração cessar e o dano for reparado antes da fiscalização.</span>}
        {l.barras.map((b) => { const m = p.reducao.medidas.find((m) => m.dispositivo.toLowerCase() === b.rotulo.toLowerCase()); return <div key={b.rotulo} className="grid grid-cols-[70px_minmax(0,1fr)_72px] items-center gap-2 text-xs">
          <span>{m ? <LinkFonte sha256={m.sha256} trecho={m.trecho}>{b.rotulo}</LinkFonte> : b.rotulo}</span>
          <span className="block h-2 bg-trilho"><span className="barra" style={{ width: `${Math.max(b.fracao * 100, 2)}%`, background: b.cor === 'teto' ? 'var(--cor-barra-teto)' : b.cor === 'media' ? 'var(--cor-barra-media)' : 'var(--cor-barra-reducao)' }} /></span>
          <span className="text-right font-bold">{b.reais != null ? brlCurto(b.reais) : '—'}</span>
        </div> })}
      </div>
      <div className={COLUNA}>
        <span className={TITULO_COLUNA}>O que fazer</span>
        {l.fazer ? <span className="text-[15px] leading-snug">✓ {l.fazer.texto} <span className="text-xs font-semibold">Sugestão</span></span> : <span className="text-[15px]">recomendação em revisão</span>}
        {l.evite && <span className="text-[15px] leading-snug text-evite">✕ {l.evite} <span className="text-xs font-semibold">Sugestão</span></span>}
        {l.proveCom && <span className="mt-1 text-[13px] leading-snug"><strong>Prove com:</strong> {l.proveCom}</span>}
      </div>
      <div className={COLUNA}>
        <span className={TITULO_COLUNA}>Defesa possível</span>
        <span className="text-[15px] leading-snug">{l.defesa.texto}</span>
        {l.defesa.origem && <span className="self-start border border-obsidian px-2 py-0.5 text-xs font-semibold">{l.defesa.origem}</span>}
        <a href={l.link} className="mt-auto text-[15px] font-semibold underline underline-offset-4">Detalhes no plano →</a>
      </div>
    </div>
  </div>
}
