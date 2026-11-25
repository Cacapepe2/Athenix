import { LinkFonte } from '../ui/LinkFonte'
import { useMemo, useState } from 'react'
import { ValorInfracao } from '../ui/ValorInfracao'
import { brlCurto, dataBR, HOJE, normaDaUrl, pct } from '../../content/plano'
import { norma as dadosDa, NORMAS, urlPlanoCompleto } from '../../content/executivo'
import { calendarioIcs, tarefasCsv } from '../../content/tarefas'
import { FILTROS_TODAS, filtrar, type BlocoPlano, type Filtros } from '../../content/filtros'
import { ComparacaoAnterior } from './ComparacaoAnterior'
import { RevisaoLocal } from './RevisaoLocal'

// Plano completo, por obrigação: blocos clicáveis; os filtros ficam no menu lateral (FiltrosMenu). Mesma lógica
// da página executiva (content/executivo.ts); a URL guarda os filtros (?norma=…&situacao=…).
const valorCurto = (b: BlocoPlano) => (b.valor ? (b.valor.reais != null ? brlCurto(b.valor.reais) : pct(b.valor.pct)) : 'a enquadrar')

function baixar(nome: string, conteudo: string, tipo: string) {
  const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }))
  const a = Object.assign(document.createElement('a'), { href: url, download: nome })
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
const slug = (t: string) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

export function BlocosObrigacoes({ todos, filtros, mudar }: { todos: BlocoPlano[]; filtros: Filtros; mudar: (f: Filtros) => void }) {
  const [aberto, setAberto] = useState<string | null>(null)
  const visiveis = useMemo(() => filtrar(todos, filtros), [todos, filtros])
  const naPagina = normaDaUrl()
  const outra = filtros.norma !== 'todas' && filtros.norma !== naPagina ? filtros.norma : null

  return <section id="obrigacoes" aria-labelledby="titulo-obrigacoes" className="space-y-4 print:hidden">
    <h2 id="titulo-obrigacoes" className="border-b-[length:var(--borda-titulo)] border-obsidian pb-3 text-[32px] leading-none font-bold ">Obrigações</h2>
      <div className="flex min-w-0 flex-col gap-3.5">
        {outra && <p className="border-[length:var(--borda-forte)] border-obsidian px-4 py-2.5 text-sm font-semibold">Mostrando obrigações da {dadosDa(outra).rotulo.replace('/2025', '').replace('/2026', '')}. O resto da página é da {dadosDa(naPagina).rotulo.replace('/2025', '').replace('/2026', '')} · <a href={urlPlanoCompleto(outra)} className="underline underline-offset-4 hover:text-acento">Ver a página da {dadosDa(outra).rotulo.replace('/2025', '').replace('/2026', '')} →</a></p>}
        <p className="text-sm" aria-live="polite">Mostrando <strong>{visiveis.length}</strong> de {todos.length} obrigações · clique num bloco para abrir · dias contados até {dataBR(HOJE)}</p>
        <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(220px,1fr))]">
          {visiveis.map((b) => <Bloco key={`${b.norma}-${b.id}`} b={b} aberta={aberto === `${b.norma}-${b.id}`} alternar={() => setAberto(aberto === `${b.norma}-${b.id}` ? null : `${b.norma}-${b.id}`)} />)}
        </div>
        {visiveis.length === 0 && <div className="flex flex-wrap items-center gap-4 border-[length:var(--borda-forte)] border-obsidian p-6 text-[15px]"><p>Nenhuma obrigação com estes filtros</p><button type="button" className="botao" onClick={() => mudar(FILTROS_TODAS)}>Mostrar todas</button></div>}
        <div className="flex flex-col gap-2">
          <span className="text-[13px] font-bold">Quem faz o quê</span>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="botao" onClick={() => baixar(`tarefas-${filtros.area === 'todas' ? 'todas-as-areas' : slug(filtros.area)}.csv`, `﻿${tarefasCsv(visiveis, filtros.area === 'todas' ? null : filtros.area)}`, 'text/csv;charset=utf-8')}>Baixar tarefas da área (CSV)</button>
            <button type="button" className="botao" onClick={() => baixar('prazos-athenix.ics', calendarioIcs(NORMAS.map((n) => ({ norma: n.id, vigencia: n.dados.norma.vigencia, blocos: visiveis.filter((b) => b.norma === n.id), trechos: Object.fromEntries(n.dados.obrigacoes.map((o) => [o.id, o.trecho ?? ''])) })), filtros.area === 'todas' ? null : filtros.area), 'text/calendar;charset=utf-8')}>Adicionar prazos ao calendário (.ics)</button>
          </div>
          <span className="text-xs">A área é sugestão: pela regra do tipo da obrigação ou, quando a regra não acha, “área sugerida (IA)”, marcada no CSV e no relatório. O arquivo sai só no seu navegador. Respeita os filtros do menu.</span>
        </div>
        <p className="text-[13px]">preliminar = enquadramento sugerido pela IA, aguardando revisão · “identificado no texto” = a norma nomeia a infração · títulos resumidos por IA · não constitui parecer jurídico.</p>
      </div>
  </section>
}

function Bloco({ b, aberta, alternar }: { b: BlocoPlano; aberta: boolean; alternar: () => void }) {
  const vencida = b.situacaoPrazo === 'vencida'
  const o = dadosDa(b.norma).dados.obrigacoes.find((x) => x.id === b.id)
  const painel = `painel-${b.norma}-${b.id}`
  return <article id={`bloco-${b.id}`} className={`flex flex-col ${aberta ? 'col-span-full' : ''}`}>
    <button type="button" className="bloco flex min-h-[150px] flex-col gap-2 p-4 text-left" aria-expanded={aberta} aria-controls={painel} onClick={alternar}>
      <span className="text-xs font-semibold">{b.normaRotulo.replace('/2025', '').replace('/2026', '')} · {b.dispositivo ?? 'dispositivo a confirmar'}</span>
      <span className="text-base leading-tight font-semibold">{b.titulo}</span>
      <span className="mt-auto flex flex-col gap-1">
        <ValorInfracao texto={valorCurto(b)} enquadrado={!!b.valor} preliminar={!!b.preliminar} />
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${vencida && !aberta ? 'text-bronze-deep' : ''}`}>
          {vencida && <span aria-hidden="true" className="inline-block h-2 w-2 rounded-full bg-acento" />}{b.prazoCurto}
        </span>
      </span>
    </button>
    <div id={painel} role="region" aria-label={`Detalhes de ${b.dispositivo ?? 'obrigação'}`} hidden={!aberta} className="border-[length:var(--borda-forte)] border-t-0 border-obsidian bg-white">
      {aberta && o && b.norma === normaDaUrl() && <div className="p-5"><RevisaoLocal o={o} /></div>}
      {aberta && o && b.norma === normaDaUrl() && <div className="p-5"><ComparacaoAnterior o={o} /></div>}
      {aberta && <div className="grid gap-6 p-5 [grid-template-columns:repeat(auto-fit,minmax(240px,1fr))]">
        <div className="flex flex-col gap-2">
          <span className="text-[13px] font-bold">O que a norma exige</span>
          <span className="text-[15px] leading-normal">{b.trecho ? `“${b.trecho.trim()}”` : b.frase}</span>
          {b.sujeitoImplicito && <span className="text-xs font-semibold">Sujeito implícito (a revisar): o texto não diz “a distribuidora”; contamos como dever dela por ser norma dirigida às distribuidoras.</span>}
          <span className="text-[13px]"><LinkFonte sha256={NORMAS.find((n) => n.id === b.norma)!.dados.norma.sha256} trecho={b.trecho}>{b.dispositivo}</LinkFonte>{b.valor ? ` · ${b.gravidadeRotulo} (${b.preliminar ? 'sugerida pela IA, aguarda revisão humana' : 'identificada no texto'})` : ' · gravidade a enquadrar'}</span>
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-[13px] font-bold">Faça</span>
          {b.fazer ? b.fazer.todas.slice(0, 2).map((a) => <span key={a} className="border-l-[length:var(--borda-titulo)] border-obsidian pl-3.5 text-[15px] leading-snug">{a}</span>) : <span className="text-[15px]">recomendação em revisão</span>}
          {b.fazer && <span className="text-xs font-semibold">Sugestão (IA), aguarda revisão humana</span>}
          {b.evite && <><span className="mt-2 text-[13px] font-bold text-evite">Evite</span><span className="border-l-[length:var(--borda-titulo)] border-evite pl-3.5 text-[15px] leading-snug">{b.evite}</span><span className="text-xs font-semibold">Sugestão (IA), aguarda revisão humana</span></>}
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
