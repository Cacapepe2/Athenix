import { motion, useMotionTemplate, useMotionValue } from 'motion/react'
import { Check, FileSearch, Gauge, ListChecks, Radar } from 'lucide-react'
import type { PointerEvent } from 'react'
import { approach } from '../../content/site'
import { Eyebrow, MaskedTitle, Reveal, RevealLi } from '../ui/Reveal'

const icons = [Radar, FileSearch, Gauge, ListChecks]
type Scope = 'base' | 'foco' | 'futuro'
const chip: Record<Scope, string> = { base: 'Base do MVP', foco: 'Foco do MVP', futuro: 'Etapa futura' }
const ease = [0.16, 1, 0.3, 1] as const

function Pillar({ i, title, text, scope }: { i: number; title: string; text: string; scope: Scope }) {
  const now = scope !== 'futuro'
  const mx = useMotionValue(-200)
  const my = useMotionValue(-200)
  const glow = useMotionTemplate`radial-gradient(260px circle at ${mx}px ${my}px, var(--cor-hover), transparent 70%)`
  const Icon = icons[i]
  const onMove = (e: PointerEvent<HTMLLIElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    mx.set(e.clientX - r.left)
    my.set(e.clientY - r.top)
  }
  return (
    <motion.li
      onPointerMove={onMove}
      onPointerLeave={() => {
        mx.set(-200)
        my.set(-200)
      }}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '0px 0px -10% 0px' }}
      transition={{ duration: 0.9, ease, delay: 0.15 + i * 0.12 }}
      whileHover={{ y: -4 }}
      className={`group relative overflow-hidden rounded-2xl border p-6 transition-colors duration-500 ${
        scope === 'foco'
          ? 'border-bronze/60 bg-ivory/[0.09] hover:border-bronze'
          : now
            ? 'border-ivory/15 bg-ivory/[0.05] hover:border-bronze/50'
            : 'border-dashed border-ivory/15 hover:border-ivory/30'
      }`}
    >
      <motion.span aria-hidden="true" style={{ background: glow }} className="pointer-events-none absolute inset-0" />
      <div className="relative">
        <div className="flex items-center justify-between">
          <span
            className={`grid h-10 w-10 place-items-center rounded-xl border ${
              now ? 'border-bronze/40 text-bronze' : 'border-ivory/15 text-ivory/50'
            }`}
          >
            <Icon className="h-5 w-5" strokeWidth={1.6} aria-hidden="true" />
          </span>
          <span className="font-display text-sm text-ivory/40 tabular-nums">0{i + 1}</span>
        </div>
        <h3 className={`font-display mt-6 text-[1.35rem] leading-tight ${now ? 'text-ivory' : 'text-ivory/75'}`}>{title}</h3>
        <p className={`mt-2.5 text-[0.9rem] leading-relaxed ${now ? 'text-ivory/70' : 'text-ivory/55'}`}>{text}</p>
        <p
          className={`mt-5 inline-flex items-center gap-1.5 px-2.5 py-1 text-[0.68rem] font-medium ${
            scope === 'foco'
              ? 'bg-bronze text-obsidian'
              : now
                ? 'bg-bronze/15 text-bronze'
                : 'border border-dashed border-ivory/20 text-ivory/55'
          }`}
        >
          {chip[scope]}
        </p>
      </div>
    </motion.li>
  )
}

export function Approach() {
  return (
    <section id="abordagem" className="on-dark px-3 py-6 sm:px-5">
      <div data-dark className="relative overflow-hidden  bg-obsidian py-24 text-ivory sm:py-28">
        <div className="relative mx-auto max-w-7xl px-5 sm:px-8">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
            <div>
              <Eyebrow tone="light">{approach.eyebrow}</Eyebrow>
              <MaskedTitle
                text={approach.title}
                className="font-display mt-5 text-[2.1rem] leading-[1.08] sm:text-[2.9rem]"
              />
            </div>
            <Reveal delay={0.1}>
              <p className="text-[1rem] leading-relaxed text-ivory/70">{approach.description}</p>
            </Reveal>
          </div>

          {/* Linha de escopo: preenchida no MVP, tracejada na visão futura */}
          <div aria-hidden="true" className="mt-16 hidden gap-4 text-[0.7rem] font-semibold lg:grid lg:grid-cols-4">
            {[approach.scopeLabels.base, approach.scopeLabels.foco, approach.scopeLabels.futuro].map((label, i) => (
              <div key={label} className={i === 0 ? 'col-span-2' : ''}>
                <p className={i < 2 ? 'text-bronze' : 'text-ivory/45'}>{label}</p>
                <div className="relative mt-3 h-px bg-ivory/10">
                  <motion.div
                    initial={{ scaleX: 0 }}
                    whileInView={{ scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 1.4, ease, delay: 0.2 + i * 0.5 }}
                    className={`absolute inset-0 origin-left ${
                      i < 2 ? 'bg-bronze' : 'bg-[repeating-linear-gradient(90deg,var(--cor-fundo)_0_6px,transparent_6px_12px)]'
                    }`}
                  />
                </div>
              </div>
            ))}
          </div>

          <ol className="mt-6 grid gap-4 sm:grid-cols-2 md:mt-5 lg:grid-cols-4">
            {approach.pillars.map((p, i) => (
              <Pillar key={p.title} i={i} {...p} />
            ))}
          </ol>

          <div className="mt-16 grid gap-6 border-t border-ivory/10 pt-10 md:grid-cols-[0.6fr_1.4fr]">
            <p className="font-display text-[1.4rem] text-ivory">{approach.principlesTitle}</p>
            <ul className="grid gap-4 sm:grid-cols-3">
              {approach.principles.map((p, i) => (
                <RevealLi key={p} delay={i * 0.1} className="flex gap-3 text-[0.92rem] leading-snug text-ivory/75">
                  <Check aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-bronze" strokeWidth={2.2} />
                  {p}
                </RevealLi>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
