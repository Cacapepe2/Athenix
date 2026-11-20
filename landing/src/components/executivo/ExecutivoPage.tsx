import { useRef, useState, type ReactNode, type Ref } from 'react'
import { Logo } from '../ui/Logo'
import { Chevron } from '../ui/Chevron'
import { Tag } from '../product/Tag'
import { BOTAO_AJUDA } from '../plano/AjudaGrupos'
import {
  NORMA_PADRAO, NORMAS, destaqueDaNorma, norma as dadosDa, prazos, queda, referenciaDoSetor, tabelaDeGrupos, top5, urlPlanoCompleto, valorGeral,
  type LinhaTop5,
} from '../../content/executivo'
import { rotuloDoGrupo } from '../../content/gravidade'
import { brlCurto, dataBR, normaDaUrl, pct, type NormaId, type PlanoDados, type Simulacao } from '../../content/plano'

// Visão executiva (/demo/executivo): quanto custa, o que vence e o que fazer, numa tela. Todos os números
// vêm de content/executivo.ts (planos gerados pelo motor); aqui só há apresentação.
const MODO = 'preliminar' as const
const PORTE_PADRAO = 'media'
const IA = 'Interpretação da IA · aguarda revisão humana'
// Terracota só no fundo de botões e do item escolhido; texto, bordas e foco em azul (index.css).
const BOTAO_ACENTO = 'inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-full bg-acento-escuro px-5 text-sm font-semibold whitespace-nowrap text-white shadow-sm hover:bg-acento-hover print:hidden'
const LINK = 'font-semibold text-slate-blue underline decoration-slate-blue/40 underline-offset-4 hover:decoration-slate-blue'
// Mesma aparência dos chips de porte da /demo: escolhido em terracota com texto branco.
const CHIP = 'inline-flex min-h-11 cursor-pointer items-center justify-center gap-1 rounded-full text-center'
const CHIP_COR = 'border border-slate-blue/40 bg-white px-4 py-1 text-sm leading-tight text-obsidian hover:border-slate-blue hover:bg-slate-blue/5 has-checked:border-transparent has-checked:bg-acento-escuro has-checked:font-semibold has-checked:text-white has-checked:shadow-sm has-checked:hover:bg-acento-escuro has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-slate-blue'
const CARTAO = 'flex flex-col rounded-2xl border border-slate-blue/30 bg-white px-4 py-3 shadow-soft sm:px-5'
const NUMERO = 'font-display mt-1 text-[2.25rem] leading-none text-obsidian sm:text-[2.6rem]'
const ROTULO_CARTAO = 'text-sm font-semibold text-slate-blue'

const emReais = (reais: number | null, p: number) => (reais != null ? brlCurto(reais) : `${pct(p)} da receita`)
const art = (d: string) => d.replace(/^Art\./, 'art.')

export function ExecutivoPage() {
  const [normaId, setNormaId] = useState<NormaId>(normaDaUrl)
  const [porteId, setPorteId] = useState(PORTE_PADRAO)
  const como = useRef<HTMLDetailsElement>(null)
  const n = dadosDa(normaId)
  const p = n.dados
  const faixas = p.simulador.faixas
  const faixa = faixas.find((f) => f.id === porteId) ?? faixas[1]
  const sim: Simulacao = { base: faixa.base, faturamento: null }
  const v = valorGeral(p, sim, MODO)
  const q = queda(p, sim, MODO)
  const pz = prazos(p)
  const linhas = top5(normaId, sim, MODO)
  const ref = referenciaDoSetor(p, v?.grupo)
  const destaque = destaqueDaNorma(p)

  const trocarNorma = (id: NormaId) => {
    setNormaId(id)
    // Link compartilhável sem recarregar a página.
    history.replaceState(history.state, '', `${location.pathname}${id === NORMA_PADRAO ? '' : `?norma=${id}`}`)
  }
  const abrirComo = () => {
    const d = como.current
    if (!d) return
    d.open = true
    d.scrollIntoView({ block: 'start' })
    d.querySelector('summary')?.focus({ preventScroll: true })
  }
  const ajuda = <button type="button" onClick={abrirComo} aria-controls="como-calculamos" aria-label="O que são os grupos de infração: abre Como calculamos" className={BOTAO_AJUDA}>?</button>
  const preliminar = <Tag kind="pending" label="preliminar" />

  return <>
    <header className="border-b border-line bg-ivory">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-2 sm:px-8">
        <div className="flex min-w-0 flex-wrap items-center gap-x-2.5">
          <a href="/" aria-label="Athenix, voltar ao início" className="inline-flex min-h-11 items-center"><Logo /></a>
          <span aria-hidden="true" className="text-2xl text-bronze-deep">·</span>
          <h1 className="font-display text-[1.6rem] leading-none whitespace-nowrap">Visão executiva</h1>
          <p className="text-sm text-ink-soft max-lg:basis-full lg:ml-3">quanto custa, o que vence e o que fazer · {p.perfil.rotulo.toLowerCase()} (não é empresa real)</p>
        </div>
        <a href={urlPlanoCompleto(normaId)} className={BOTAO_ACENTO}>Ver plano completo →</a>
      </div>
    </header>

    <main id="executivo" className="mx-auto max-w-7xl space-y-4 px-4 pt-3 pb-8 sm:px-8 print:space-y-3 print:pt-0">
      <p className="hidden text-sm print:block">{n.rotulo} · {n.resumo} · porte {faixa.rotulo} (~{brlCurto(faixa.base)} de receita operacional líquida anual, faixa ilustrativa)</p>

      <div className="flex flex-wrap items-end gap-x-8 gap-y-3 print:hidden">
        <fieldset className="min-w-0 max-sm:w-full">
          <legend className="text-xs font-semibold text-ink-soft">Norma</legend>
          <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            {NORMAS.map((x) => <label key={x.id} className={`flex min-h-11 cursor-pointer flex-col justify-center rounded-2xl text-left ${CHIP_COR}`}>
              <input type="radio" className="sr-only" name="norma" value={x.id} checked={normaId === x.id} onChange={() => trocarNorma(x.id)} />
              <span className="font-semibold">{x.rotulo}</span><span className="text-xs">{x.resumo}</span>
            </label>)}
          </div>
        </fieldset>
        <fieldset className="min-w-0 max-sm:w-full">
          <legend className="flex flex-wrap items-center gap-2 text-xs font-semibold text-ink-soft">Porte da distribuidora (receita operacional líquida anual) <Tag kind="estimate" label="faixa ilustrativa" /></legend>
          <div className="mt-1 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
            {faixas.map((x) => <label key={x.id} className={`${CHIP} ${CHIP_COR}`}>
              <input type="radio" className="sr-only" name="porte" value={x.id} checked={faixa.id === x.id} onChange={() => setPorteId(x.id)} />
              <span>{x.rotulo}</span> <span className="whitespace-nowrap">~{brlCurto(x.base)}</span>
            </label>)}
          </div>
        </fieldset>
      </div>

      <p className="rounded-2xl border-2 border-slate-blue bg-white px-4 py-2 text-base font-semibold text-slate-blue sm:text-lg" aria-label="Sobre a norma escolhida"><span className="text-ink-soft">{n.rotulo}:</span> {destaque.texto}</p>

      <section aria-label="Os três números" aria-live="polite" className="grid gap-3 md:grid-cols-3">
        <article className={CARTAO} aria-labelledby="cartao-exposicao">
          <h2 id="cartao-exposicao" className={ROTULO_CARTAO}>Exposição por infração</h2>
          {v ? <>
            <p className={NUMERO}>até {emReais(v.reais, v.pct)} <span className="font-sans text-base text-ink-soft">por infração</span></p>
            <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-soft"><span>{rotuloDoGrupo(v.grupo)} · até {pct(v.pct)} da receita</span>{ajuda}{v.origem === 'sugerido' && preliminar}</p>
            {v.origem === 'sugerido' && <p className="mt-2"><Tag kind="ai" label={IA} /></p>}
          </> : <>
            <p className={NUMERO}>a enquadrar</p>
            <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-soft"><span>o texto desta norma não nomeia a infração e não há sugestão de enquadramento: sem valor a mostrar</span>{ajuda}</p>
          </>}
        </article>

        <article className={CARTAO} aria-labelledby="cartao-queda">
          <h2 id="cartao-queda" className={ROTULO_CARTAO}>Quanto pode cair agindo agora</h2>
          {q && v ? <>
            <p className={NUMERO}>até {pct(q.reducaoPct)} menos</p>
            <p className="mt-2 text-sm text-ink-soft">{q.de != null ? brlCurto(q.de) : '—'} → {q.para != null ? brlCurto(q.para) : '—'} por infração se cessar a infração e reparar todo o dano antes da fiscalização{v.origem !== 'identificado' && <> {preliminar}</>}</p>
            <details className="mt-1 text-sm">
              <summary className={`inline-flex min-h-11 cursor-pointer items-center gap-1 ${LINK} print:hidden`}>ver a norma: {art(q.dispositivo)} da REN 846<Chevron className="h-4 w-4" /></summary>
              <blockquote className="border-l-2 border-bronze bg-ivory p-2 text-xs">“{q.trecho.trim()}”</blockquote>
              <p className="mt-1 text-xs break-all text-ink-soft">{q.dispositivo} · {q.fonte} · SHA-256 {q.sha256}</p>
            </details>
          </> : <p className={NUMERO}>a avaliar</p>}
        </article>

        <article className={CARTAO} aria-labelledby="cartao-prazos">
          <h2 id="cartao-prazos" className={ROTULO_CARTAO}>Prazos</h2>
          <p className={NUMERO}>{pz.vencidas} {pz.vencidas === 1 ? 'vencida' : 'vencidas'}</p>
          <p className="mt-2 text-sm text-ink-soft">{pz.vencidas === 1 ? 'obrigação com prazo já vencido' : 'obrigações com prazo já vencido'}; {pz.proxima ? `próxima vence em ${pz.proxima.dias} dias (${dataBR(pz.proxima.data)})` : 'nenhuma com data a vencer'}</p>
          <p className="mt-1 text-xs text-ink-soft">datas provisórias, a confirmar; dias contados até {dataBR(p.perfil.data_referencia)}</p>
        </article>
      </section>

      <section aria-labelledby="top5">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h2 id="top5" className="font-display text-2xl leading-tight">{linhas.length} obrigações para olhar primeiro</h2>
          <p className="text-xs text-ink-soft">vencidas primeiro, depois o maior valor por infração</p>
        </div>
        <div className="mt-2 md:rounded-2xl md:border md:border-slate-blue/30 md:bg-white md:px-4">
          <table className="w-full border-collapse text-left text-sm max-md:block md:table-fixed">
            <thead className="max-md:sr-only">
              <tr className="border-b border-slate-blue/30 text-xs text-ink-soft">
                <th scope="col" className="w-[28%] py-2 pr-3 font-semibold">Obrigação</th>
                <th scope="col" className="w-[10%] py-2 pr-3 font-semibold">Prazo</th>
                <th scope="col" className="w-[19%] py-2 pr-3 font-semibold"><span className="inline-flex items-center gap-2 whitespace-nowrap">Gravidade e valor por infração{ajuda}</span></th>
                <th scope="col" className="w-[24%] py-2 pr-3 font-semibold">O que fazer</th>
                <th scope="col" className="w-[12%] py-2 pr-3 font-semibold">Defesa possível</th>
                <th scope="col" className="w-[7%] py-2 font-semibold"><span className="sr-only">Detalhes</span></th>
              </tr>
            </thead>
            <tbody className="max-md:block max-md:space-y-3">{linhas.map((l) => <Linha key={l.id} l={l} preliminar={preliminar} />)}</tbody>
          </table>
        </div>
        <Legenda linhas={linhas} preliminar={preliminar} />
      </section>

      <p className="text-sm"><span className="font-semibold">Referência do setor:</span> {ref.texto}. <span className="text-xs text-ink-soft">{ref.nota[0].toUpperCase() + ref.nota.slice(1)}.</span></p>

      <ComoCalculamos ref={como} p={p} />

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4 text-sm text-ink-soft">
        <p>Iniciativa em validação · valores ilustrativos · não constitui parecer jurídico. {p.perfil.aviso}</p>
        <a href={urlPlanoCompleto(normaId)} className={BOTAO_ACENTO}>Ver plano completo →</a>
      </footer>
    </main>
  </>
}

const CELULA = 'align-top leading-snug max-md:block md:py-2 md:pr-3'
const ROTULO_MOBILE = 'block text-xs font-semibold text-ink-soft md:hidden'

/** Uma obrigação: linha da tabela no desktop, cartão com rótulos abaixo de 768 px. */
function Linha({ l, preliminar }: { l: LinhaTop5; preliminar: ReactNode }) {
  const grupo = l.valor ? rotuloDoGrupo(l.valor.grupo) : undefined
  return <tr className="border-b border-line last:border-b-0 max-md:block max-md:space-y-2 max-md:rounded-2xl max-md:border max-md:border-slate-blue/30 max-md:bg-white max-md:p-4 max-md:last:border-b">
    <td className={CELULA}>
      <span className={ROTULO_MOBILE}>Obrigação</span>
      <span className="leading-snug font-medium [overflow-wrap:anywhere]" title={l.fraseOriginal}>{l.frase}</span>
      <span className="text-xs whitespace-nowrap text-ink-soft"> · {l.dispositivo ?? 'dispositivo a confirmar'}</span>
    </td>
    <td className={CELULA}><span className={ROTULO_MOBILE}>Prazo</span><span className={l.situacao === 'vencida' ? 'font-semibold' : ''}>{l.prazo}</span></td>
    <td className={CELULA}><span className={ROTULO_MOBILE}>Gravidade e valor por infração</span>
      <span title={grupo}>{l.gravidade} · {l.textoValor}</span>{l.preliminar && <> {preliminar}</>}</td>
    <td className={CELULA}><span className={ROTULO_MOBILE}>O que fazer</span>
      {l.fazer ? <>{l.fazer.texto}{l.fazer.preliminar && <> {preliminar}</>}</> : <span className="text-ink-soft">definir com a equipe responsável</span>}</td>
    <td className={CELULA}><span className={ROTULO_MOBILE}>Defesa possível</span>
      {l.defesa.texto}{l.defesa.origem && <> <Tag kind={l.defesa.origem === 'no texto' ? 'source' : 'review'} label={l.defesa.origem} /></>}</td>
    <td className="align-top max-md:block md:py-1.5">
      <a href={l.link} className={`inline-flex min-h-11 items-center whitespace-nowrap ${LINK} print:hidden`}>detalhes →<span className="sr-only"> da obrigação {l.dispositivo ?? ''}</span></a>
    </td>
  </tr>
}

/** O que cada etiqueta quer dizer, só quando ela aparece. */
function Legenda({ linhas, preliminar }: { linhas: LinhaTop5[]; preliminar: ReactNode }) {
  const sugerido = linhas.some((l) => l.valor?.origem === 'sugerido')
  const semValor = linhas.some((l) => !l.valor)
  const fazer = linhas.some((l) => l.fazer?.preliminar)
  if (!sugerido && !semValor && !fazer) return null
  return <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-ink-soft">
    {preliminar}
    {sugerido && <span className="inline-flex flex-wrap items-center gap-1">no valor: enquadramento sugerido pela IA <Tag kind="ai" label={IA} />;</span>}
    {semValor && <span>“a enquadrar”: o texto não nomeia a infração e não há sugestão, então não mostramos valor;</span>}
    {fazer && <span>em “O que fazer”: tipo da obrigação ainda a revisar.</span>}
  </p>
}

/** Grupos de gravidade, teto de cada um (com o dispositivo) e atenuantes, todos vindos do plano. */
function ComoCalculamos({ ref, p }: { ref: Ref<HTMLDetailsElement>; p: PlanoDados }) {
  const t = tabelaDeGrupos(p)
  const espontanea = p.reducao.medidas.find((m) => m.cenario === 'espontanea')
  const ateTn = p.reducao.medidas.find((m) => m.cenario === 'ate_tn')
  return <details ref={ref} id="como-calculamos" className="rounded-2xl border border-slate-blue/30 bg-white hover:border-slate-blue open:border-line print:hidden">
    <summary className="flex min-h-11 cursor-pointer items-center gap-3 rounded-2xl px-4 py-2 hover:bg-slate-blue/5">
      <span className="flex min-w-0 flex-wrap items-baseline gap-x-3"><span className="font-semibold text-slate-blue">Como calculamos</span><span className="text-xs text-ink-soft">grupos de gravidade, teto de cada um e atenuantes</span></span><Chevron />
    </summary>
    <div className="space-y-3 px-4 pb-4 text-sm leading-relaxed">
      <p>A ANEEL (a agência que regula o setor elétrico) classifica cada infração em 5 grupos de gravidade (REN 846, o regulamento de multas). Cada grupo tem um teto de multa em % da receita da empresa.</p>
      <ul className="grid gap-2 sm:grid-cols-5" aria-label="Teto de multa por grupo">
        {t.grupos.map((g) => <li key={g.grupo} className="rounded-xl border border-line bg-ivory px-3 py-2" title={g.trecho ?? undefined}>
          <span className="block">{g.rotulo}</span>
          <strong className="block">{g.pct != null ? `até ${pct(g.pct)} da receita` : 'sem teto citado'}</strong>
          <span className="block text-xs text-ink-soft">REN 846, {g.dispositivo ?? 'dispositivo a confirmar'}</span>
        </li>)}
      </ul>
      {t.tetoLegal && <p>Por infração, nunca somadas. Acima de todos, o limite legal de {t.tetoLegal.pct != null ? pct(t.tetoLegal.pct) : '—'} do faturamento ({t.tetoLegal.dispositivo}). O valor de cada obrigação é o teto do grupo sobre a receita operacional líquida do porte escolhido, sem agravantes. “Preliminar”: enquadramento sugerido pela IA (<Tag kind="ai" label={IA} />), ainda sem revisão humana. Sem enquadramento, não há valor.</p>}
      {espontanea?.percentual != null && <p>Atenuantes da própria norma reduzem o valor: até {pct(espontanea.percentual)} se cessar a infração e reparar todo o dano antes de a ANEEL comunicar a fiscalização ou lavrar o Termo de Notificação ({espontanea.dispositivo}){ateTn?.percentual != null && <>; {pct(ateTn.percentual)} até o prazo do Termo de Notificação, a notificação que a ANEEL envia antes do auto ({ateTn.dispositivo})</>}. Vale um atenuante só.</p>}
    </div>
  </details>
}
