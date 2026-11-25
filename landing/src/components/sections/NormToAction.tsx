import { useRef, useState } from 'react'
import { AnimatePresence, motion, useMotionValueEvent, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { story } from '../../content/site'
import { stepAt } from '../../lib/text'
import { scrollToY } from '../../lib/scroll'
import { Eyebrow } from '../ui/Reveal'
import { StoryStage } from '../product/StoryStage'

const ease = [0.16, 1, 0.3, 1] as const
const n = story.steps.length

function Heading() {
  return (
    <>
      <Eyebrow>{story.eyebrow}</Eyebrow>
      <h2 className="font-display mt-4 text-[2rem] leading-[1.08] text-obsidian sm:text-[2.6rem]">{story.title}</h2>
      <p className="mt-4 max-w-md text-[0.98rem] leading-relaxed text-ink-soft">{story.intro}</p>
    </>
  )
}

/** Narrativa fixa (sticky) em cinco estados, avançada pela rolagem. */
export function NormToAction() {
  const reduce = useReducedMotion()
  const section = useRef<HTMLElement>(null)
  const [step, setStep] = useState(0)
  const { scrollYProgress } = useScroll({ target: section, offset: ['start start', 'end end'] })
  useMotionValueEvent(scrollYProgress, 'change', (p) => setStep(stepAt(p, n)))
  // Progresso dentro da etapa atual (0–1), derivado só do scroll para não depender de estado capturado.
  const local = useTransform(scrollYProgress, (p) => (p * n >= n ? 1 : Math.max(0, p * n - Math.floor(p * n))))

  const goTo = (i: number) => {
    const el = section.current
    if (!el) return
    scrollToY(el.offsetTop + ((i + 0.5) / n) * (el.offsetHeight - window.innerHeight), !!reduce)
  }

  return (
    <div id="da-norma-a-acao">
      <div className="mx-auto max-w-7xl px-5 pt-20 sm:px-8 lg:hidden">
        <Heading />
      </div>
    <section ref={section} className="relative h-[460vh] bg-ivory" aria-label={story.eyebrow}>
      <div className="sticky top-0 flex h-svh flex-col pt-20 pb-5 lg:pt-16 lg:pb-0">
        <div className="mx-auto grid h-full min-h-0 w-full max-w-7xl grid-cols-1 max-lg:grid-rows-[auto_minmax(0,1fr)] gap-5 px-5 sm:px-8 lg:grid-cols-[0.82fr_1.18fr] lg:items-center lg:gap-14">
          <div className="lg:py-10">
            <div className="hidden lg:block">
              <Heading />
            </div>

            <ol className="mt-0 lg:mt-10">
              {story.steps.map((s, i) => {
                const active = i === step
                return (
                  <li key={s.title} className={`${active ? '' : 'max-lg:hidden'} border-line lg:border-t lg:last:border-b`}>
                    <button
                      type="button"
                      onClick={() => goTo(i)}
                      aria-current={active ? 'step' : undefined}
                      className="group flex w-full items-baseline gap-4 py-1 text-left lg:py-3.5"
                    >
                      <span
                        className={`font-display w-6 text-sm tabular-nums transition-colors ${active ? 'text-bronze-deep' : 'text-ink-soft/60'}`}
                      >
                        0{i + 1}
                      </span>
                      <span
                        className={`font-display text-[1.25rem] leading-tight transition-colors duration-300 lg:text-[1.35rem] ${
                          active ? 'text-obsidian' : 'text-ink-soft/70 group-hover:text-obsidian'
                        }`}
                      >
                        {s.title}
                      </span>
                      <span className="ml-auto shrink-0 text-[0.7rem] text-ink-soft lg:hidden">
                        {i + 1} de {n}
                      </span>
                    </button>
                    <AnimatePresence initial={false}>
                      {active ? (
                        <motion.div
                          key="txt"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.45, ease }}
                          className="overflow-hidden"
                        >
                          <p className="pb-4 pl-10 text-[0.92rem] leading-relaxed text-ink-soft">{s.text}</p>
                          <div className="mb-4 ml-10 h-px bg-line max-lg:hidden">
                            <motion.div style={{ scaleX: local }} className="h-px origin-left bg-bronze-deep" />
                          </div>
                        </motion.div>
                      ) : (
                        <p key="sr" className="sr-only">
                          {s.text}
                        </p>
                      )}
                    </AnimatePresence>
                  </li>
                )
              })}
            </ol>

            <div aria-hidden="true" className="mt-1 flex gap-1.5 lg:hidden">
              {story.steps.map((s, i) => (
                <span key={s.title} className={`h-1 flex-1 ${i <= step ? 'bg-bronze-deep' : 'bg-line'}`} />
              ))}
            </div>
          </div>

          <div className="min-h-0 flex-1 lg:h-[min(600px,78vh)]">
            <StoryStage step={step} />
          </div>
        </div>
      </div>
    </section>
    </div>
  )
}
