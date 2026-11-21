import { useRef } from 'react'
import { motion, useReducedMotion, useScroll, useTransform, type MotionValue } from 'motion/react'
import { stakes } from '../../content/site'
import { Eyebrow, MaskedTitle, Reveal, RevealLi } from '../ui/Reveal'

const n = stakes.chain.length

function Node({ label, i, p }: { label: string; i: number; p: MotionValue<number> }) {
  const t = i / (n - 1)
  const aceso = useTransform(p, [t - 0.06, t], [0, 1])
  const text = useTransform(p, [t - 0.06, t], [0.55, 1])
  return (
    <li className="relative flex items-center gap-4 md:flex-col md:items-start md:gap-5">
      <span className="relative z-10 h-4 w-4 shrink-0 rounded-full border-2 border-obsidian bg-ivory">
        <motion.span style={{ opacity: aceso }} className="absolute inset-0 rounded-full bg-obsidian" />
      </span>
      <motion.span style={{ opacity: text }} className="text-obsidian font-displaytext-[1.2rem] leading-tight md:text-[1.35rem]">
        {label}
      </motion.span>
    </li>
  )
}

/** Cadeia de consequências desenhada conforme a rolagem. */
export function Stakes() {
  const reduce = useReducedMotion()
  const chain = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: chain, offset: ['start 0.85', 'start 0.35'] })
  const p = useTransform(scrollYProgress, (v) => (reduce ? 1 : v))

  return (
    <section id="por-que-importa" className="bg-stone/45 py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="max-w-3xl">
          <Eyebrow>{stakes.eyebrow}</Eyebrow>
          <MaskedTitle
            text={stakes.title}
            className="font-display mt-5 text-[2.1rem] leading-[1.08] text-obsidian sm:text-[2.9rem]"
          />
        </div>

        <div ref={chain} className="relative mt-16">
          <div aria-hidden="true" className="absolute top-[7px] right-[calc(25%-1.125rem-8px)] left-2 hidden h-px bg-line md:block">
            <motion.div style={{ scaleX: p }} className="h-full origin-left bg-slate-blue" />
          </div>
          <div aria-hidden="true" className="absolute top-2 bottom-2 left-[7px] w-px bg-line md:hidden">
            <motion.div style={{ scaleY: p }} className="h-full origin-top bg-slate-blue" />
          </div>
          <ol className="grid gap-7 md:grid-cols-4 md:gap-6">
            {stakes.chain.map((c, i) => (
              <Node key={c} label={c} i={i} p={p} />
            ))}
          </ol>
        </div>

        <ul className="mt-16 grid border-t border-obsidian/15 sm:grid-cols-2 lg:grid-cols-4">
          {stakes.consequences.map((c, i) => (
            <RevealLi
              key={c.title}
              delay={0.1 + i * 0.08}
              className="border-b border-line py-6 sm:pr-6 lg:border-r lg:border-b-0 lg:px-6 lg:first:pl-0 lg:last:border-r-0"
            >
              <h3 className="text-[1rem] font-semibold text-obsidian">{c.title}</h3>
              <p className="mt-1.5 text-[0.92rem] leading-relaxed text-ink-soft">{c.text}</p>
            </RevealLi>
          ))}
        </ul>

        <Reveal delay={0.1}>
          <p className="font-display mt-14 max-w-2xl text-[1.45rem] leading-snug text-obsidian ">{stakes.note}</p>
        </Reveal>
      </div>
    </section>
  )
}
