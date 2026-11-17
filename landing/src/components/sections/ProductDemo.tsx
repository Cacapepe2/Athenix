import { useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowLeft, ArrowRight, Check, Info, RotateCcw, X } from 'lucide-react'
import { demo } from '../../content/site'
import { articleById, changes, demoNorm, impactAreas, obligations, type RiskLevel } from '../../content/demo'
import { DocumentView } from '../product/DocumentView'
import { Tag } from '../product/Tag'
import { Eyebrow, MaskedTitle, Reveal } from '../ui/Reveal'

const ease = [0.16, 1, 0.3, 1] as const
type Decision = 'accepted' | 'rejected' | undefined

const levelStyle: Record<RiskLevel, { bar: string; w: string }> = {
  Alta: { bar: 'bg-obsidian', w: '100%' },
  Média: { bar: 'bg-slate-blue', w: '62%' },
  Baixa: { bar: 'bg-bronze', w: '28%' },
}

function PanelTitle({ title, tag }: { title: string; tag?: ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h3 className="font-display text-[1.35rem] text-obsidian">{title}</h3>
      {tag}
    </div>
  )
}

function NormPanel() {
  const meta = [
    ['Órgão', demoNorm.issuer],
    ['Publicação', demoNorm.published],
    ['Vigência', demoNorm.effective],
    ['Impressão digital', `${demoNorm.fingerprint} (ilustrativa)`],
    ['Origem', 'Documento fictício criado para esta demonstração'],
  ]
  return (
    <div className="grid gap-6 md:grid-cols-[1fr_260px]">
      <div>
        <PanelTitle title="Documento original" tag={<Tag kind="source" />} />
        <DocumentView />
      </div>
      <dl className="space-y-3 self-start rounded-xl bg-stone/60 p-4 text-[0.82rem]">
        {meta.map(([k, v]) => (
          <div key={k}>
            <dt className="text-[0.68rem] font-semibold tracking-[0.14em] text-bronze-deep uppercase">{k}</dt>
            <dd className="mt-0.5 text-obsidian">{v}</dd>
          </div>
        ))}
        <p className="border-t border-line pt-3 text-[0.75rem] leading-snug text-ink-soft">
          O original é preservado sem alteração. Tudo o que vem depois aponta para ele.
        </p>
      </dl>
    </div>
  )
}

function SummaryPanel() {
  const [sel, setSel] = useState(changes[0].id)
  const change = changes.find((c) => c.id === sel)!
  const art = articleById(change.articleId)
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div>
        <PanelTitle title="O que mudou" tag={<Tag kind="ai" />} />
        <ul className="space-y-2">
          {changes.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                aria-pressed={sel === c.id}
                onClick={() => setSel(c.id)}
                className={`w-full rounded-xl border p-3.5 text-left transition-colors ${
                  sel === c.id ? 'border-slate-blue bg-slate-blue/[0.06]' : 'border-line bg-white hover:border-obsidian/25'
                }`}
              >
                <span className="block text-[0.9rem] font-semibold text-obsidian">{c.title}</span>
                <span className="mt-1 block text-[0.8rem] leading-snug text-ink-soft">{c.detail}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <PanelTitle title="De onde vem" tag={<Tag kind="source" />} />
        <AnimatePresence mode="wait">
          <motion.blockquote
            key={art.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.35, ease }}
            className="paper rounded-xl border border-line p-5"
          >
            <p className="text-[0.7rem] font-semibold tracking-[0.14em] text-bronze-deep uppercase">
              {demoNorm.kind} {demoNorm.number} · {art.label}
            </p>
            <p className="font-display mt-2 text-[1.12rem] leading-relaxed text-obsidian">“{art.text}”</p>
          </motion.blockquote>
        </AnimatePresence>
        <p className="mt-3 text-[0.78rem] leading-snug text-ink-soft">
          O resumo à esquerda é interpretação. O texto acima é a norma, citada literalmente.
        </p>
      </div>
    </div>
  )
}

function ObligationsPanel({
  decisions,
  decide,
}: {
  decisions: Record<string, Decision>
  decide: (id: string, d: Decision) => void
}) {
  const [sel, setSel] = useState(obligations[0].id)
  const o = obligations.find((x) => x.id === sel)!
  const d = decisions[o.id]
  return (
    <div className="grid gap-6 md:grid-cols-[0.9fr_1.1fr]">
      <div>
        <PanelTitle title="Obrigações candidatas" />
        <ul className="space-y-2">
          {obligations.map((x, i) => (
            <li key={x.id}>
              <button
                type="button"
                aria-pressed={sel === x.id}
                onClick={() => setSel(x.id)}
                className={`flex w-full gap-3 rounded-xl border p-3.5 text-left transition-colors ${
                  sel === x.id ? 'border-slate-blue bg-slate-blue/[0.06]' : 'border-line bg-white hover:border-obsidian/25'
                }`}
              >
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-blue text-[0.72rem] font-semibold text-ivory">
                  {i + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[0.88rem] leading-snug font-semibold text-obsidian">{x.title}</span>
                  <span className="mt-1.5 flex flex-wrap gap-1.5">
                    <Tag kind={decisions[x.id] ?? 'review'} />
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <PanelTitle title="Fundamento e revisão" tag={<Tag kind="source" label={`${articleById(o.articleId).label} · trecho literal`} />} />
        <DocumentView focusId={o.articleId} marks={{ [o.articleId]: o.anchor }} animateMarks key={o.id} />
        <div className="mt-4 rounded-xl border border-line bg-white p-4">
          <p className="text-[0.82rem] text-ink-soft">
            <Tag kind="ai" className="mr-2" />
            {o.title}.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {d ? (
              <button
                type="button"
                onClick={() => decide(o.id, undefined)}
                className="inline-flex min-h-10 items-center gap-1.5 rounded-full border border-line px-4 text-[0.82rem] text-obsidian hover:border-obsidian/30"
              >
                <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" /> Desfazer decisão
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => decide(o.id, 'accepted')}
                  className="inline-flex min-h-10 items-center gap-1.5 rounded-full bg-slate-blue px-4 text-[0.82rem] font-medium text-ivory hover:bg-obsidian"
                >
                  <Check className="h-3.5 w-3.5" aria-hidden="true" /> Aceitar
                </button>
                <button
                  type="button"
                  onClick={() => decide(o.id, 'rejected')}
                  className="inline-flex min-h-10 items-center gap-1.5 rounded-full border border-line px-4 text-[0.82rem] text-obsidian hover:border-obsidian/30"
                >
                  <X className="h-3.5 w-3.5" aria-hidden="true" /> Rejeitar
                </button>
              </>
            )}
            <p aria-live="polite" className="text-[0.75rem] text-ink-soft">
              {d === 'accepted' && 'Aceita por você (simulação, nada é salvo).'}
              {d === 'rejected' && 'Rejeitada por você (simulação, nada é salvo).'}
              {!d && 'Nenhuma obrigação vale sem decisão humana.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function DeadlinesPanel() {
  return (
    <div>
      <PanelTitle title="Prazos e responsáveis" tag={<Tag kind="ai" label="Responsáveis sugeridos pela IA" />} />
      <div className="overflow-hidden rounded-xl border border-line bg-white">
        <table className="w-full text-left text-[0.84rem]">
          <thead className="bg-stone/60 text-[0.68rem] font-semibold tracking-[0.12em] text-bronze-deep uppercase max-md:sr-only">
            <tr>
              <th className="px-4 py-3 font-semibold">Obrigação</th>
              <th className="px-4 py-3 font-semibold">Prazo</th>
              <th className="px-4 py-3 font-semibold">Tipo</th>
              <th className="px-4 py-3 font-semibold">Responsável sugerido</th>
              <th className="px-4 py-3 font-semibold">Fundamento</th>
            </tr>
          </thead>
          <tbody>
            {obligations.map((o, i) => (
              <motion.tr
                key={o.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease, delay: 0.08 * i }}
                className="border-t border-line align-top max-md:grid max-md:gap-1 max-md:px-4 max-md:py-4"
              >
                <td className="font-semibold text-obsidian md:px-4 md:py-3.5">{o.short}</td>
                <td className="text-obsidian md:px-4 md:py-3.5">
                  {o.deadline}
                  {o.pending && (
                    <span className="mt-1.5 block">
                      <Tag kind="pending" />
                      <span className="mt-1 block text-[0.75rem] leading-snug text-pending">{o.pending}</span>
                    </span>
                  )}
                </td>
                <td className="text-ink-soft md:px-4 md:py-3.5">{o.deadlineKind}</td>
                <td className="text-ink-soft md:px-4 md:py-3.5">{o.owner}</td>
                <td className="text-bronze-deep md:px-4 md:py-3.5">{articleById(o.articleId).label}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[0.78rem] text-ink-soft">
        Quando o texto não permite fixar uma data, ela fica pendente para revisão. Nenhuma data é presumida.
      </p>
    </div>
  )
}

function ImpactsPanel() {
  return (
    <div>
      <PanelTitle title="Riscos e impactos preliminares" tag={<Tag kind="review" label="Requer validação da equipe" />} />
      <div className="overflow-x-auto rounded-xl border border-line bg-white">
        <table className="w-full min-w-[560px] text-left text-[0.82rem]">
          <thead className="bg-stone/60 text-[0.68rem] tracking-[0.12em] text-bronze-deep uppercase">
            <tr>
              <th className="px-4 py-3 font-semibold">Obrigação</th>
              {impactAreas.map((a) => (
                <th key={a} className="px-4 py-3 font-semibold">
                  {a}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {obligations.map((o, r) => (
              <tr key={o.id} className="border-t border-line">
                <th scope="row" className="px-4 py-3.5 font-semibold text-obsidian">
                  {o.short}
                  <span className="mt-1 block max-w-[220px] text-[0.72rem] leading-snug font-normal text-ink-soft">
                    {o.impactNote}
                  </span>
                </th>
                {impactAreas.map((a, c) => (
                  <td key={a} className="px-4 py-3.5 align-top">
                    <span className="block text-[0.75rem] text-obsidian">{o.risks[a]}</span>
                    <span className="mt-1.5 block h-1.5 w-20 rounded-full bg-stone" aria-hidden="true">
                      <motion.span
                        className={`block h-full rounded-full ${levelStyle[o.risks[a]].bar}`}
                        initial={{ width: 0 }}
                        animate={{ width: levelStyle[o.risks[a]].w }}
                        transition={{ duration: 0.8, ease, delay: 0.15 + r * 0.1 + c * 0.05 }}
                      />
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[0.78rem] leading-snug text-ink-soft">
        Classificação qualitativa e ilustrativa. Estimativas financeiras dependem de dados da empresa e não são
        apresentadas sem eles.
      </p>
    </div>
  )
}

export function ProductDemo() {
  const [tab, setTab] = useState(0)
  const [dir, setDir] = useState(1)
  const [decisions, setDecisions] = useState<Record<string, Decision>>({})
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])
  const count = demo.tabs.length

  const select = (i: number, focus = false) => {
    const next = (i + count) % count
    setDir(next > tab ? 1 : -1)
    setTab(next)
    if (focus) tabRefs.current[next]?.focus()
  }
  const onKeyDown = (e: KeyboardEvent) => {
    const map: Record<string, number> = { ArrowRight: tab + 1, ArrowLeft: tab - 1, Home: 0, End: count - 1 }
    if (e.key in map) {
      e.preventDefault()
      select(map[e.key], true)
    }
  }
  const decide = (id: string, d: Decision) => setDecisions((s) => ({ ...s, [id]: d }))

  const panels = [
    <NormPanel key="0" />,
    <SummaryPanel key="1" />,
    <ObligationsPanel key="2" decisions={decisions} decide={decide} />,
    <DeadlinesPanel key="3" />,
    <ImpactsPanel key="4" />,
  ]

  return (
    <section id="demonstracao" className="relative bg-stone/55 py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <Eyebrow>{demo.eyebrow}</Eyebrow>
            <MaskedTitle
              text={demo.title}
              className="font-display mt-5 text-[2.1rem] leading-[1.08] text-obsidian sm:text-[2.9rem]"
            />
            <Reveal delay={0.1}>
              <p className="mt-5 max-w-xl text-[1.02rem] leading-relaxed text-ink-soft">{demo.description}</p>
            </Reveal>
          </div>
          <Reveal delay={0.2}>
            <p className="flex gap-3 rounded-2xl border border-dashed border-bronze-deep/40 bg-ivory/70 p-4 text-[0.84rem] leading-snug text-ink-soft">
              <Info aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-bronze-deep" />
              {demo.disclaimer}
            </p>
          </Reveal>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.985 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: '0px 0px -10% 0px' }}
          transition={{ duration: 1, ease }}
          className="mt-12 overflow-hidden rounded-[26px] border border-line bg-ivory shadow-float"
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-white px-5 py-4 sm:px-7">
            <div>
              <p className="font-display text-[1.2rem] leading-tight text-obsidian">
                {demoNorm.kind} {demoNorm.number}
              </p>
              <p className="mt-0.5 text-[0.78rem] text-ink-soft">{demoNorm.subject}</p>
            </div>
            <Tag kind="fictional" label={demoNorm.badge} />
          </div>

          <div
            role="tablist"
            aria-label="Etapas da análise demonstrativa"
            onKeyDown={onKeyDown}
            className="flex overflow-x-auto border-b border-line bg-white px-3 sm:px-5"
          >
            {demo.tabs.map((t, i) => (
              <button
                key={t}
                ref={(el) => {
                  tabRefs.current[i] = el
                }}
                role="tab"
                id={`tab-${i}`}
                aria-selected={tab === i}
                aria-controls={`painel-${i}`}
                tabIndex={tab === i ? 0 : -1}
                onClick={() => select(i)}
                className={`relative flex min-h-12 shrink-0 items-center gap-2 px-3 text-[0.86rem] whitespace-nowrap transition-colors sm:px-4 ${
                  tab === i ? 'font-semibold text-obsidian' : 'text-ink-soft hover:text-obsidian'
                }`}
              >
                <span
                  className={`grid h-5 w-5 place-items-center rounded-full text-[0.66rem] tabular-nums ${
                    tab === i ? 'bg-slate-blue text-ivory' : 'bg-stone text-ink-soft'
                  }`}
                >
                  {i + 1}
                </span>
                {t}
                {tab === i && (
                  <motion.span layoutId="tab-underline" className="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-slate-blue" />
                )}
              </button>
            ))}
          </div>

          <div
            role="tabpanel"
            id={`painel-${tab}`}
            aria-labelledby={`tab-${tab}`}
            tabIndex={0}
            className="relative min-h-[460px] overflow-hidden p-5 sm:p-7"
          >
            <AnimatePresence mode="wait" custom={dir} initial={false}>
              <motion.div
                key={tab}
                custom={dir}
                variants={{
                  enter: (d: number) => ({ opacity: 0, x: 28 * d }),
                  center: { opacity: 1, x: 0 },
                  exit: (d: number) => ({ opacity: 0, x: -20 * d }),
                }}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.4, ease }}
              >
                {panels[tab]}
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="flex items-center justify-between border-t border-line bg-white px-5 py-3 sm:px-7">
            <button
              type="button"
              onClick={() => select(tab - 1)}
              disabled={tab === 0}
              className="inline-flex min-h-10 items-center gap-1.5 rounded-full px-3 text-[0.84rem] text-ink-soft hover:text-obsidian disabled:opacity-35"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Etapa anterior
            </button>
            <button
              type="button"
              onClick={() => select(tab + 1)}
              disabled={tab === count - 1}
              className="inline-flex min-h-10 items-center gap-1.5 rounded-full bg-obsidian px-4 text-[0.84rem] font-medium text-ivory hover:bg-slate-blue disabled:opacity-35"
            >
              Próxima etapa <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
