import { useState } from 'react'
import { NORMA_PADRAO, NORMAS, norma as dadosDa, prazos, queda, top5, urlPlanoCompleto, valorGeral, type LinhaTop5 } from '../../content/executivo'
import { brlCurto, normaDaUrl, type NormaId, type Simulacao } from '../../content/plano'

// Visão executiva (/demo/executivo): três números e até cinco blocos clicáveis. Muito pouco texto; o resto
// fica no plano completo. Todos os números vêm de content/executivo.ts (planos gerados pelo motor).
const MODO = 'preliminar' as const
const PORTE_PADRAO = 'media'
const LINK = 'font-semibold underline underline-offset-4 hover:text-acento'
const GRANDE = 'block text-[64px] leading-[0.95] font-bold tracking-[-0.05em] sm:text-[80px] lg:text-[96px]'
const LEGENDA = 'text-[17px] font-semibold'

const valorDoBloco = (l: LinhaTop5) => (l.valor?.reais != null ? `${brlCurto(l.valor.reais)}${l.preliminar ? '*' : ''}` : 'a enquadrar')

export function ExecutivoPage() {
  const [normaId, setNormaId] = useState<NormaId>(normaDaUrl)
  const [porteId, setPorteId] = useState(PORTE_PADRAO)
  const [aberto, setAberto] = useState<string | null>(null)
  const [ultimo, setUltimo] = useState<string | null>(null) // o painel, ao fechar, mantém o último conteúdo
  const n = dadosDa(normaId)
  const p = n.dados
  const faixa = p.simulador.faixas.find((f) => f.id === porteId) ?? p.simulador.faixas[1]
  const sim: Simulacao = { base: faixa.base, faturamento: null }
  const v = valorGeral(p, sim, MODO)
  const q = queda(p, sim, MODO)
  const pz = prazos(p)
  const linhas = top5(normaId, sim, MODO)
  const sel = linhas.find((l) => l.id === ultimo) ?? null
  const preliminar = v?.origem === 'sugerido'

  const trocarNorma = (id: NormaId) => {
    setNormaId(id)
    setAberto(null)
    setUltimo(null)
    history.replaceState(history.state, '', `${location.pathname}${id === NORMA_PADRAO ? '' : `?norma=${id}`}`)
  }
  const alternar = (id: string) => {
    setAberto(aberto === id ? null : id)
    setUltimo(id)
  }

  return <main id="executivo" className="mx-auto flex max-w-[1200px] flex-col gap-10 px-4 pt-6 pb-12 sm:px-8">
    <header className="flex flex-wrap items-center justify-between gap-4 border-b-[length:var(--borda-titulo)] border-obsidian pb-4">
      <a href="/" aria-label="Athenix, voltar ao início" className="text-[28px] font-bold tracking-[-0.03em]">Athenix</a>
      <div className="flex flex-wrap items-center gap-3.5">
        <div role="group" aria-label="Norma" className="flex">
          {NORMAS.map((x) => <button key={x.id} type="button" className="seg" aria-pressed={normaId === x.id} onClick={() => trocarNorma(x.id)}>{x.rotulo.replace('/2025', '').replace('/2026', '')}</button>)}
        </div>
        <div role="group" aria-label="Porte da distribuidora (receita operacional líquida anual)" className="flex">
          {p.simulador.faixas.map((x) => <button key={x.id} type="button" className="seg" aria-pressed={faixa.id === x.id} onClick={() => setPorteId(x.id)}>{x.base / 1e9} bi</button>)}
        </div>
      </div>
      <a href={urlPlanoCompleto(normaId)} className={`text-[15px] ${LINK}`}>Plano completo →</a>
    </header>

    <section aria-label="Resumo" aria-live="polite" className="grid gap-8 [grid-template-columns:repeat(auto-fit,minmax(260px,1fr))]">
      <div className="flex flex-col gap-1.5">
        <span className={`${GRANDE} text-acento`}>{v?.reais != null ? <><span className="mr-2 text-[0.4em] align-baseline">R$</span>{brlCurto(v.reais).replace('R$ ', '')}</> : 'a enquadrar'}</span>
        <span className={LEGENDA}>por infração{preliminar ? '*' : ''}</span>
      </div>
      <div className="flex flex-col gap-1.5">
        <span className={GRANDE}>{q ? `−${Math.round(q.reducaoPct)}%` : '—'}</span>
        <span className={LEGENDA}>se agir antes da fiscalização</span>
      </div>
      <div className="flex flex-col gap-1.5">
        {pz.vencidas > 0
          ? <><span className={GRANDE}>{pz.vencidas}</span><span className={LEGENDA}>{pz.vencidas === 1 ? 'obrigação vencida' : 'obrigações vencidas'}</span></>
          : pz.proxima
            ? <><span className={GRANDE}>{pz.proxima.dias} dias</span><span className={LEGENDA}>até o próximo prazo</span></>
            : <><span className={GRANDE}>—</span><span className={LEGENDA}>nenhum prazo a vencer</span></>}
      </div>
    </section>

    <section aria-labelledby="comece-por" className="flex flex-col gap-3.5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="comece-por" className="text-[17px] font-bold">Comece por</h2>
        <span className="text-sm">Toque num item para ver o que fazer</span>
      </div>
      <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(190px,1fr))]">
        {linhas.map((l) => {
          const aberta = aberto === l.id
          const vencida = l.situacao === 'vencida'
          return <button key={l.id} type="button" className="bloco flex min-h-[196px] flex-col gap-2.5 p-4 text-left" aria-expanded={aberta} aria-controls="painel" onClick={() => alternar(l.id)}>
            <span className={`inline-flex items-center gap-1.5 text-xs font-bold ${vencida && !aberta ? 'text-bronze-deep' : ''}`}>
              <span aria-hidden="true" className={`inline-block h-2 w-2 rounded-full ${vencida ? 'bg-acento' : aberta ? 'bg-white' : 'bg-obsidian'}`} />{l.prazoCurto}
            </span>
            <span className="text-base leading-tight font-semibold">{l.titulo}</span>
            <span className="mt-auto text-[30px] font-bold tracking-[-0.03em]">{valorDoBloco(l)}</span>
            <span className="flex items-center justify-between border-t border-current pt-2.5 text-[13px] font-semibold">
              <span>{aberta ? 'Fechar' : 'Ver o que fazer'}</span><span aria-hidden="true" className="seta text-lg">{aberta ? '↑' : '↓'}</span>
            </span>
          </button>
        })}
      </div>

      <div id="painel" role="region" aria-label="Detalhes da obrigação" className="painel" data-aberto={aberto ? 'true' : 'false'}>
        <div className="painel-miolo" inert={!aberto}>
          {sel && <Painel l={sel} fechar={() => setAberto(null)} />}
        </div>
      </div>
    </section>

    <footer className="flex flex-wrap justify-between gap-3 border-t border-obsidian pt-3.5 text-[13px]">
      <span>* preliminar · valores ilustrativos · não é parecer jurídico</span>
      <a href={urlPlanoCompleto(normaId)} className="font-semibold">Plano completo →</a>
    </footer>
  </main>
}

const COLUNA = 'flex flex-col gap-2 border-r border-line px-6 py-5 last:border-r-0'
const TITULO_COLUNA = 'text-[13px] font-bold'

function Painel({ l, fechar }: { l: LinhaTop5; fechar: () => void }) {
  return <div className="painel-in">
    <div className="flex flex-wrap items-start justify-between gap-4 border-b-[length:var(--borda-forte)] border-obsidian px-6 py-5">
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="text-[13px] font-semibold">{l.dispositivo ?? 'dispositivo a confirmar'}</span>
        <span className="text-[22px] leading-tight font-bold tracking-[-0.02em]">{l.frase}</span>
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
        <span className="text-[15px]">{l.valor ? `${l.gravidadeRotulo} · ${l.preliminar ? 'preliminar' : 'identificada no texto'}` : 'gravidade a enquadrar'}</span>
        {l.barras.map((b) => <div key={b.rotulo} className="grid grid-cols-[70px_minmax(0,1fr)_72px] items-center gap-2 text-xs">
          <span>{b.rotulo}</span>
          <span className="block h-2 bg-trilho"><span className="barra" style={{ width: `${Math.max(b.fracao * 100, 2)}%`, background: b.cor === 'teto' ? 'var(--cor-barra-teto)' : b.cor === 'media' ? 'var(--cor-barra-media)' : 'var(--cor-barra-reducao)' }} /></span>
          <span className="text-right font-bold">{b.reais != null ? brlCurto(b.reais) : '—'}</span>
        </div>)}
      </div>
      <div className={COLUNA}>
        <span className={TITULO_COLUNA}>O que fazer</span>
        {l.fazer ? <span className="text-[15px] leading-snug">✓ {l.fazer.texto} <span className="text-xs font-semibold">Sugestão</span></span> : <span className="text-[15px]">recomendação em revisão</span>}
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
