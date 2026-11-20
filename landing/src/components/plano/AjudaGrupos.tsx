import { useEffect, useId, useRef, useState } from 'react'
import { X } from 'lucide-react'
import { tabelaDeGrupos } from '../../content/executivo'
import { pct, type PlanoDados } from '../../content/plano'

/** Botão "?" de 24 px com área de toque de 44 px (pseudo-elemento), para ficar no meio do texto. */
export const BOTAO_AJUDA = "relative inline-grid h-6 w-6 shrink-0 cursor-pointer place-items-center rounded-full border border-slate-blue/60 bg-white text-xs leading-none font-bold text-slate-blue before:absolute before:-inset-2.5 before:content-[''] hover:border-slate-blue hover:bg-slate-blue/10 print:hidden"

/** "?" ao lado de "infração grave (Grupo IV)": abre a tabela dos 5 grupos da REN 846 com o teto de cada um,
 *  vinda do plano (dispositivo e trecho literal). Só spans: cabe dentro de um parágrafo sem quebrar o HTML. */
export function AjudaGrupos({ p }: { p: PlanoDados }) {
  const [aberto, setAberto] = useState(false)
  const id = useId()
  const botao = useRef<HTMLButtonElement>(null)
  const caixa = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    if (!aberto) return
    caixa.current?.focus()
    const fechar = () => { setAberto(false); botao.current?.focus() }
    const tecla = (e: KeyboardEvent) => e.key === 'Escape' && fechar()
    const fora = (e: MouseEvent) => !caixa.current?.contains(e.target as Node) && !botao.current?.contains(e.target as Node) && setAberto(false)
    document.addEventListener('keydown', tecla)
    document.addEventListener('mousedown', fora)
    return () => { document.removeEventListener('keydown', tecla); document.removeEventListener('mousedown', fora) }
  }, [aberto])
  const t = tabelaDeGrupos(p)
  return <span className="inline-flex align-middle">
    <button ref={botao} type="button" aria-expanded={aberto} aria-controls={id} aria-label="O que são os grupos de infração" onClick={() => setAberto(!aberto)} className={BOTAO_AJUDA}>?</button>
    {aberto && <span ref={caixa} id={id} role="dialog" aria-label="Grupos de infração da REN 846" tabIndex={-1}
      className="fixed top-1/2 left-1/2 z-50 block max-h-[85vh] w-[min(28rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl border-2 border-slate-blue bg-white p-5 text-left text-sm font-normal text-obsidian shadow-float">
      <span className="flex items-start justify-between gap-3">
        <span className="block font-semibold text-slate-blue">Grupos de infração da REN 846 (o regulamento de multas da ANEEL)</span>
        <button type="button" onClick={() => { setAberto(false); botao.current?.focus() }} aria-label="Fechar" className="-m-2 inline-grid h-11 w-11 shrink-0 cursor-pointer place-items-center rounded-full text-slate-blue hover:bg-slate-blue/10"><X aria-hidden="true" className="h-5 w-5" /></button>
      </span>
      <span className="mt-1 block text-ink-soft">Cada grupo tem um teto de multa em % da receita da empresa, por infração.</span>
      <span className="mt-3 block divide-y divide-line">
        {t.grupos.map((g) => <span key={g.grupo} className="flex items-baseline justify-between gap-3 py-1.5" title={g.trecho ?? undefined}>
          <span>{g.rotulo}</span>
          <span className="text-right whitespace-nowrap"><strong>{g.pct != null ? `até ${pct(g.pct)}` : 'sem teto citado'}</strong> <span className="block text-xs text-ink-soft">{g.dispositivo ?? 'dispositivo a confirmar'}</span></span>
        </span>)}
      </span>
      {t.tetoLegal && <span className="mt-2 block text-xs text-ink-soft">Limite legal de {t.tetoLegal.pct != null ? pct(t.tetoLegal.pct) : '—'} do faturamento ({t.tetoLegal.dispositivo}).</span>}
    </span>}
  </span>
}
