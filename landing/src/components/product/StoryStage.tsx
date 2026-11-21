import { AnimatePresence, LayoutGroup, motion } from 'motion/react'
import { CalendarClock, UserRound } from 'lucide-react'
import { DocumentView } from './DocumentView'
import { Tag } from './Tag'
import { articleById, brl, changes, demoNorm, obligations, priorities, profile } from '../../content/demo'

const ease = [0.16, 1, 0.3, 1] as const
const stageArticles = obligations.map((o) => articleById(o.articleId))
const allMarks = Object.fromEntries(obligations.map((o) => [o.articleId, o.anchor]))
const numbers = Object.fromEntries(obligations.map((o, i) => [o.articleId, String(i + 1)]))
const maior = Math.max(...obligations.map((o) => o.impact.max))

function Badge({ articleId }: { articleId: string }) {
  return (
    <motion.span
      layoutId={`mark-${articleId}`}
      className="grid h-6 w-6 shrink-0 place-items-center bg-slate-blue text-[0.7rem] font-semibold text-ivory"
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
      className="flex h-full flex-col overflow-hidden  border border-line bg-white/75 backdrop-blur"
    >
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 sm:px-5">
        <span className="truncate text-[0.72rem] text-ink-soft">
          <span className="font-semibold text-obsidian">Athenix</span> · RN ANEEL 1.137/2025
        </span>
        <span className="flex items-center gap-2">
          <Tag kind="estimate" label={demoNorm.badge} />
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
                    <span className="inline-flex items-center gap-1.5 bg-slate-blue px-2.5 py-1 font-medium text-ivory">
                      <span className="h-1.5 w-1.5 rounded-full bg-bronze" />
                      Documento carregado
                    </span>
                    Vigência {demoNorm.effective} · {demoNorm.fingerprint}
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
                  <p className="font-display text-lg text-obsidian">Alertas da norma</p>
                  <Tag kind="rule" label="Por regra" />
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
                      <p className="flex items-center justify-between gap-2 text-[0.8rem] font-semibold text-obsidian">
                        {c.title}
                        <span className="text-[0.66rem] font-normal text-bronze-deep">{articleById(c.articleId).label}</span>
                      </p>
                      <p className="mt-1 line-clamp-3 text-[0.74rem] leading-snug text-ink-soft">{c.detail}</p>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="obligations" {...panel}>
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg text-obsidian">Obrigações para revisar</p>
                  <Tag kind="review" />
                </div>
                <ul className="mt-3 space-y-2.5">
                  {obligations.map((o) => (
                    <li key={o.id} className="flex gap-3 rounded-xl border border-line bg-white p-3">
                      <Badge articleId={o.articleId} />
                      <span className="min-w-0">
                        <span className="block text-[0.8rem] leading-snug font-semibold text-obsidian">{o.short}</span>
                        <span className="mt-1 block text-[0.68rem] text-ink-soft">
                          Fundamento: {articleById(o.articleId).label} · trecho literal
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
                  <p className="font-display text-lg text-obsidian">Prazos</p>
                  <Tag kind="rule" label="Provisórios" />
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
                          {o.subject}
                        </span>
                        {o.pending && <Tag kind="pending" label="Sem data no texto" />}
                      </motion.div>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div key="impacts" {...panel}>
                <div className="flex items-center justify-between">
                  <p className="font-display text-lg text-obsidian">Impacto e prioridade</p>
                  <Tag kind="estimate" />
                </div>
                <div className="mt-3 overflow-hidden rounded-xl border border-line bg-white">
                  {priorities.map((o, r) => (
                    <div key={o.id} className="border-b border-line/70 px-3 py-2.5 last:border-0">
                      <div className="flex items-center justify-between gap-2 text-[0.72rem]">
                        <span className="flex min-w-0 items-center gap-2 font-medium text-obsidian">
                          <Badge articleId={o.articleId} />
                          <span className="truncate">{o.short}</span>
                        </span>
                        <span className="shrink-0 text-ink-soft">de advertência até {brl(o.impact.max)}</span>
                      </div>
                      <span className="mt-2 block h-1.5 bg-stone">
                        <motion.span
                          className="block h-full bg-slate-blue"
                          initial={{ width: 0 }}
                          animate={{ width: `${(100 * o.impact.max) / maior}%` }}
                          transition={{ duration: 0.8, ease, delay: 0.3 + r * 0.12 }}
                        />
                      </span>
                      <span className="mt-1 block text-[0.64rem] text-ink-soft">
                        {o.verifyFraming ? 'verificar enquadramento' : `${o.position}ª na fila`} · confiança {o.confidence} ·{' '}
                        {o.deadline.split(',')[0]}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="mt-2.5 text-[0.66rem] leading-snug text-ink-soft">
                  Faixa de 0 até o máximo, com perfil ilustrativo ({profile.label}, base de {brl(profile.base)}). Premissas,
                  confiança e fonte em cada item da demonstração.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </LayoutGroup>
    </div>
  )
}
