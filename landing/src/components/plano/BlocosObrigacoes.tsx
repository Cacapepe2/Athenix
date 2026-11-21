import { useMemo, useState } from 'react'
import { brlCurto, pct, type Modo, type Simulacao } from '../../content/plano'
import { FILTROS_INICIAIS, OPCOES, blocosDoPlano, filtrar, filtrosDaUrl, urlComFiltros, type BlocoPlano, type Filtros } from '../../content/filtros'

// Plano completo, por obrigação: filtros à esquerda (empilham no celular) e blocos clicáveis. Mesma lógica
// da página executiva (content/executivo.ts); a URL guarda os filtros (?norma=…&situacao=…).
const valorCurto = (b: BlocoPlano) => (b.valor ? (b.valor.reais != null ? `${brlCurto(b.valor.reais)}${b.preliminar ? '*' : ''}` : `${pct(b.valor.pct)}${b.preliminar ? '*' : ''}`) : 'a enquadrar')

export function BlocosObrigacoes({ sim, modo }: { sim: Simulacao | null; modo: Modo }) {
  const [filtros, setFiltros] = useState<Filtros>(() => (typeof location === 'undefined' ? FILTROS_INICIAIS : filtrosDaUrl(location.search)))
  const [aberto, setAberto] = useState<string | null>(null)
  const todos = useMemo(() => blocosDoPlano(sim, modo), [sim, modo])
  const visiveis = filtrar(todos, filtros)

  const mudar = (novo: Filtros) => {
    setFiltros(novo)
    setAberto(null)
    history.replaceState(history.state, '', `${location.pathname}${urlComFiltros(location.search, novo)}${location.hash}`)
  }
  const temFiltro = OPCOES.some((o) => filtros[o.chave] !== 'todas')

  return <section id="obrigacoes" aria-labelledby="titulo-obrigacoes" className="space-y-4 print:hidden">
    <h2 id="titulo-obrigacoes" className="border-b-[length:var(--borda-titulo)] border-obsidian pb-3 text-[32px] leading-none font-bold ">Obrigações</h2>
    <div className="flex flex-wrap items-start gap-8">
      <aside aria-label="Filtros" className="flex max-w-full flex-[1_1_220px] flex-col gap-5 sm:max-w-[260px]">
        {OPCOES.map((g) => <fieldset key={g.chave} className="pilha flex flex-col">
          <legend className="mb-1.5 p-0 text-[13px] font-bold">{g.titulo}</legend>
          {g.opcoes.map((o) => <button key={o.valor} type="button" className="seg" aria-pressed={filtros[g.chave] === o.valor} onClick={() => mudar({ ...filtros, [g.chave]: o.valor })}>{o.rotulo}</button>)}
        </fieldset>)}
        <button type="button" disabled={!temFiltro} onClick={() => mudar(FILTROS_INICIAIS)} className="min-h-11 cursor-pointer py-2.5 text-left text-sm font-semibold underline underline-offset-4 disabled:cursor-default disabled:no-underline disabled:opacity-60">Limpar filtros</button>
      </aside>

      <div className="flex min-w-0 flex-[999_1_560px] flex-col gap-3.5">
        <p className="text-sm" aria-live="polite">Mostrando <strong>{visiveis.length}</strong> de {todos.length} obrigações · clique num bloco para abrir</p>
        <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(220px,1fr))]">
          {visiveis.map((b) => <Bloco key={`${b.norma}-${b.id}`} b={b} aberta={aberto === `${b.norma}-${b.id}`} alternar={() => setAberto(aberto === `${b.norma}-${b.id}` ? null : `${b.norma}-${b.id}`)} />)}
        </div>
        {visiveis.length === 0 && <p className="border-[length:var(--borda-forte)] border-obsidian p-6 text-[15px]">Nenhuma obrigação com esses filtros. Limpe um dos filtros à esquerda.</p>}
        <p className="text-[13px]">* preliminar = enquadramento sugerido pela IA, aguardando revisão · “identificado no texto” = a norma nomeia a infração · valores ilustrativos · não constitui parecer jurídico.</p>
      </div>
    </div>
  </section>
}

function Bloco({ b, aberta, alternar }: { b: BlocoPlano; aberta: boolean; alternar: () => void }) {
  const vencida = b.situacaoPrazo === 'vencida'
  const painel = `painel-${b.norma}-${b.id}`
  return <article id={`bloco-${b.id}`} className={`flex flex-col ${aberta ? 'col-span-full' : ''}`}>
    <button type="button" className="bloco flex min-h-[150px] flex-col gap-2 p-4 text-left" aria-expanded={aberta} aria-controls={painel} onClick={alternar}>
      <span className="text-xs font-semibold">{b.normaRotulo.replace('/2025', '').replace('/2026', '')} · {b.dispositivo ?? 'dispositivo a confirmar'}</span>
      <span className="text-base leading-tight font-semibold">{b.titulo}</span>
      <span className="mt-auto flex flex-col gap-1">
        <span className="text-[28px] font-bold whitespace-nowrap">{valorCurto(b)}</span>
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${vencida && !aberta ? 'text-bronze-deep' : ''}`}>
          {vencida && <span aria-hidden="true" className="inline-block h-2 w-2 rounded-full bg-acento" />}{b.prazoCurto}
        </span>
      </span>
    </button>
    <div id={painel} role="region" aria-label={`Detalhes de ${b.dispositivo ?? 'obrigação'}`} hidden={!aberta} className="border-[length:var(--borda-forte)] border-t-0 border-obsidian bg-white">
      {aberta && <div className="grid gap-6 p-5 [grid-template-columns:repeat(auto-fit,minmax(240px,1fr))]">
        <div className="flex flex-col gap-2">
          <span className="text-[13px] font-bold">O que a norma exige</span>
          <span className="text-[15px] leading-normal">{b.trecho ? `“${b.trecho.trim()}”` : b.frase}</span>
          <span className="text-[13px]">{b.dispositivo}{b.valor ? ` · ${b.gravidadeRotulo} (${b.preliminar ? 'sugerida pela IA, aguarda revisão humana' : 'identificada no texto'})` : ' · gravidade a enquadrar'}</span>
          <span className="text-xs">Título do bloco: resumo gerado por IA, a revisar.</span>
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-[13px] font-bold">Faça</span>
          {b.fazer ? b.fazer.todas.slice(0, 2).map((a) => <span key={a} className="border-l-[length:var(--borda-titulo)] border-obsidian pl-3.5 text-[15px] leading-snug">{a}</span>) : <span className="text-[15px]">recomendação em revisão</span>}
          {b.fazer && <span className="text-xs font-semibold">Sugestão (IA), aguarda revisão humana</span>}
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-[13px] font-bold">O que provar</span>
          <span className="text-[15px] leading-snug">{b.proveCom ?? '—'}</span>
          <span className="mt-2 text-[13px] font-bold">Defesa possível</span>
          <span className="text-[15px] leading-snug">{b.defesa.texto}{b.defesa.origem ? ` (${b.defesa.origem})` : ''}</span>
          {b.reduzidoReais != null && <span className="mt-2 text-[13px]">Se regularizar antes da fiscalização: {brlCurto(b.reduzidoReais)}</span>}
        </div>
      </div>}
    </div>
  </article>
}
