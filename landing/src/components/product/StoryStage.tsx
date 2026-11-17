import { AnimatePresence, LayoutGroup, motion } from 'motion/react'
import { CalendarClock, UserRound } from 'lucide-react'
import { DocumentView } from './DocumentView'
import { Tag } from './Tag'
import { articleById, changes, demoNorm, impactAreas, obligations, type RiskLevel } from '../../content/demo'

const ease = [0.16, 1, 0.3, 1] as const
const stageArticles = ['art3', 'art5', 'art7', 'art9'].map(articleById)
const allMarks = Object.fromEntries(obligations.map((o) => [o.articleId, o.anchor]))
const numbers = Object.fromEntries(obligations.map((o, i) => [o.articleId, String(i + 1)]))
const levelWidth: Record<RiskLevel, string> = { Alta: '100%', Média: '62%', Baixa: '28%' }

function Badge({ articleId }: { articleId: string }) {
  return (
    <motion.span
      layoutId={`mark-${articleId}`}
      className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-blue text-[0.7rem] font-semibold text-ivory"
    >
      {numbers[articleId]}
    </motion.span>
  )
}

const panel = {
  initial: { opacity: 0, x: 24 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.6, ease } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.25 } },
}

/** Cena ilustrativa (decorativa) da seção "Da norma à ação"; o texto da etapa ativa fica fora dela. */
export function StoryStage({ step }: { step: number }) {
  const showDoc = step <= 2
  return (
    <div
      aria-hidden="true"
      className="flex h-full flex-col overflow-hidden rounded-[26px] border border-line bg-white/75 shadow-float backdrop-blur"
    >
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 sm:px-5">
        <span className="truncate text-[0.72rem] text-ink-soft">
          <span className="font-semibold text-obsidian">Athenix</span> · análise demonstrativa
        </span>
        <span className="flex items-center gap-2">
          <Tag kind="fictional" label={demoNorm.badge} />
          <span className="text-[0.68rem] text-ink-soft tabular-nums">{step + 1}/5</span>
        </span>
      </div>

      <LayoutGroup>
        <div
          className={`relative grid min-h-0 flex-1 gap-4 p-4 sm:p-5 ${
            step === 1 || step === 2 ? 'sm:grid-cols-[1fr_1fr]' : 'grid-cols-1'
          }`}
        >
          <AnimatePresence mode="popLayout">
            {showDoc && (
              <motion.div
                key="doc"
                layout
                initial={{ opacity: 0, y: 80, rotate: -2.5, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, rotate: 0, scale: 1 }}
                exit={{ opacity: 0, x: -40, transition: { duration: 0.35 } }}
                transition={{ duration: 0.9, ease }}
                className={`relative min-h-0 overflow-hidden [mask-image:linear-gradient(black_80%,transparent)] ${
                  step === 0 ? 'mx-auto w-full max-w-md' : ''
                } ${step === 2 ? 'max-sm:hidden' : ''}`}
              >
                {step === 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6, duration: 0.6, ease }}
                    className="mb-3 flex flex-wrap items-center gap-2 text-[0.68rem] text-ink-soft"
                  >
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-blue px-2.5 py-1 font-medium text-ivory">
                      <span className="h-1.5 w-1.5 rounded-full bg-bronze" />
                      Nova publicação
                    </span>
                    Publicada em {demoNorm.published} · {demoNorm.fingerprint}
                  </motion.div>
                )}
                <DocumentView
                  articles={stageArticles}
                  marks={step >= 1 ? allMarks : undefined}
                  markLabels={step === 1 ? numbers : undefined}
                  animateMarks={step === 1}
                />
              </motion.div>
            )}

            {step === 1 && (
              <motion.div key="summary" {...panel} className="max-sm:hidden">
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg text-obsidian">O que mudou</p>
                  <Tag kind="ai" />
                </div>
                <ul className="mt-3 space-y-2.5">
                  {changes.map((c, i) => (
                    <motion.li
                      key={c.id}
                      initial={{ clipPath: 'inset(0 100% 0 0)' }}
                      animate={{ clipPath: 'inset(0 0% 0 0)' }}
                      transition={{ duration: 0.8, ease, delay: 0.3 + i * 0.18 }}
                      className="rounded-xl border border-line bg-white p-3"
                    >
                      <p className="flex items-center justify-between text-[0.8rem] font-semibold text-obsidian">
                        {c.title}
                        <span className="text-[0.66rem] font-normal text-bronze-deep">{articleById(c.articleId).label}</span>
                      </p>
                      <p className="mt-1 text-[0.74rem] leading-snug text-ink-soft">{c.detail}</p>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="obligations" {...panel}>
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg text-obsidian">Obrigações candidatas</p>
                  <Tag kind="review" />
                </div>
                <ul className="mt-3 space-y-2.5">
                  {obligations.map((o) => (
                    <li key={o.id} className="flex gap-3 rounded-xl border border-line bg-white p-3">
                      <Badge articleId={o.articleId} />
                      <span className="min-w-0">
                        <span className="block text-[0.8rem] leading-snug font-semibold text-obsidian">{o.title}</span>
                        <span className="mt-1 block text-[0.68rem] text-ink-soft">
                          Fundamento: {articleById(o.articleId).label} · <span className="text-bronze-deep">“{o.anchor}”</span>
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="deadlines" {...panel} className="min-h-0">
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg text-obsidian">Prazos e responsáveis</p>
                  <Tag kind="ai" label="Sugestão da IA" />
                </div>
                <ul className="mt-3 space-y-2.5">
                  {obligations.map((o, i) => (
                    <li key={o.id} className="rounded-xl border border-line bg-white p-3">
                      <div className="flex items-center gap-3">
                        <Badge articleId={o.articleId} />
                        <span className="text-[0.82rem] font-semibold text-obsidian">{o.short}</span>
                      </div>
                      <motion.div
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, ease, delay: 0.35 + i * 0.15 }}
                        className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1.5 pl-9 text-[0.72rem] text-ink-soft"
                      >
                        <span className="inline-flex items-center gap-1.5">
                          <CalendarClock className="h-3.5 w-3.5 text-slate-blue" />
                          {o.deadline}
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                          <UserRound className="h-3.5 w-3.5 text-slate-blue" />
                          {o.owner}
                        </span>
                        {o.pending && <Tag kind="pending" label="Primeira data pendente" />}
                      </motion.div>
                    </li>
                  ))}
                </ul>
                <div className="mt-5 max-sm:hidden">
                  <p className="text-[0.62rem] font-semibold tracking-[0.16em] text-bronze-deep uppercase">Linha do tempo</p>
                  <div className="relative mt-4 grid grid-cols-3 text-[0.68rem]">
                    <motion.span
                      className="absolute top-[5px] left-1 h-px w-[66%] origin-left bg-slate-blue"
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ duration: 1, ease, delay: 0.6 }}
                    />
                    <span className="absolute top-[5px] right-0 left-[67%] h-px border-t border-dashed border-pending/60" />
                    {[
                      { d: demoNorm.published, l: 'Publicação' },
                      { d: demoNorm.effective, l: 'Início da vigência' },
                      { d: 'A definir', l: '1º relatório anual', pending: true },
                    ].map((m) => (
                      <span key={m.l} className="relative">
                        <span
                          className={`block h-[11px] w-[11px] rounded-full border-2 ${m.pending ? 'border-pending bg-white' : 'border-slate-blue bg-slate-blue'}`}
                        />
                        <span className={`mt-2 block font-semibold ${m.pending ? 'text-pending' : 'text-obsidian'}`}>{m.d}</span>
                        <span className="block text-ink-soft">{m.l}</span>
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div key="impacts" {...panel}>
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg text-obsidian">Impactos preliminares</p>
                  <Tag kind="review" label="Requer validação" />
                </div>
                <div className="mt-3 overflow-hidden rounded-xl border border-line bg-white">
                  <div className="grid grid-cols-[minmax(0,1.25fr)_repeat(4,minmax(0,1fr))] gap-2 border-b border-line px-3 py-2 text-[0.6rem] font-semibold text-ink-soft">
                    <span />
                    {impactAreas.map((a) => (
                      <span key={a} className="truncate">
                        {a}
                      </span>
                    ))}
                  </div>
                  {obligations.map((o, r) => (
                    <div
                      key={o.id}
                      className="grid grid-cols-[minmax(0,1.25fr)_repeat(4,minmax(0,1fr))] items-center gap-2 border-b border-line/70 px-3 py-2.5 last:border-0"
                    >
                      <span className="flex items-center gap-2 text-[0.72rem] font-medium text-obsidian">
                        <Badge articleId={o.articleId} />
                        <span className="truncate max-sm:hidden">{o.short}</span>
                      </span>
                      {impactAreas.map((a, c) => (
                        <span key={a} className="h-1.5 rounded-full bg-stone">
                          <motion.span
                            className={`block h-full rounded-full ${o.risks[a] === 'Alta' ? 'bg-obsidian' : o.risks[a] === 'Média' ? 'bg-slate-blue' : 'bg-bronze'}`}
                            initial={{ width: 0 }}
                            animate={{ width: levelWidth[o.risks[a]] }}
                            transition={{ duration: 0.8, ease, delay: 0.3 + r * 0.12 + c * 0.06 }}
                          />
                        </span>
                      ))}
                    </div>
                  ))}
                </div>
                <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[0.66rem] text-ink-soft">
                  {[['bg-obsidian', 'Alta'], ['bg-slate-blue', 'Média'], ['bg-bronze', 'Baixa']].map(([c, l]) => (
                    <span key={l} className="inline-flex items-center gap-1.5">
                      <span className={`h-1.5 w-3 rounded-full ${c}`} />
                      {l}
                    </span>
                  ))}
                  <span>· classificação qualitativa e ilustrativa</span>
                </div>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, ease, delay: 0.9 }}
                  className="mt-4 rounded-xl border border-line bg-stone/50 p-3.5 max-sm:hidden"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[0.62rem] font-semibold tracking-[0.16em] text-bronze-deep uppercase">Ponto de atenção</span>
                    <Tag kind="source" label={`Base: ${articleById('art9').label}`} />
                  </div>
                  <p className="mt-1.5 text-[0.76rem] leading-snug text-obsidian">{obligations[0].impactNote}</p>
                  <p className="mt-1.5 text-[0.68rem] text-ink-soft">
                    Magnitude financeira não estimada: depende de dados da empresa e da validação da equipe.
                  </p>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </LayoutGroup>
    </div>
  )
}
