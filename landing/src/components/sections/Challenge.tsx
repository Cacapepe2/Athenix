import { useEffect, useRef, type RefObject } from 'react'
import { motion, useReducedMotion, useScroll, useTransform, type MotionValue } from 'motion/react'
import { FileText } from 'lucide-react'
import { challenge } from '../../content/site'
import { Eyebrow, MaskedTitle, Reveal } from '../ui/Reveal'

// Posições dispersas (px num campo de ~560px de largura); escaladas pela largura real.
const scatter = [
  { x: -150, y: -40, r: -9 },
  { x: 140, y: -120, r: 7 },
  { x: -120, y: 120, r: 5 },
  { x: 160, y: 30, r: -6 },
  { x: -170, y: -150, r: 4 },
  { x: 130, y: 150, r: -8 },
  { x: -40, y: -190, r: 10 },
  { x: 30, y: 200, r: -4 },
]
const ROW = 40

const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2)

function Chip({ label, i, n, p, k }: { label: string; i: number; n: number; p: MotionValue<number>; k: RefObject<number> }) {
  const s = scatter[i % scatter.length]
  const t = (v: number) => easeInOut(Math.min(1, Math.max(0, v)))
  const finalY = (i - (n - 1) / 2) * ROW + 18
  const x = useTransform(p, (v) => s.x * k.current * (1 - t(v)))
  const y = useTransform(p, (v) => s.y * k.current * (1 - t(v)) + finalY * t(v))
  const rotate = useTransform(p, (v) => s.r * (1 - t(v)))
  return (
    <motion.li
      style={{ x, y, rotate }}
      className="absolute top-1/2 left-1/2 -mt-[17px] -ml-[110px] flex h-[34px] w-[220px] items-center gap-2.5 rounded-lg border border-line bg-white px-3 text-[0.8rem] text-obsidian "
    >
      <FileText aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-bronze-deep" strokeWidth={1.8} />
      <span className="truncate">{label}</span>
    </motion.li>
  )
}

function SourceField() {
  const reduce = useReducedMotion()
  const box = useRef<HTMLDivElement>(null)
  const k = useRef(1)
  const { scrollYProgress } = useScroll({ target: box, offset: ['start 0.85', 'center 0.45'] })
  const p = useTransform(scrollYProgress, (v) => (reduce ? 1 : v))
  const headerOpacity = useTransform(p, [0.75, 1], [0, 1])
  const lineScale = useTransform(p, [0.8, 1], [0, 1])
  const n = challenge.sources.length

  useEffect(() => {
    const el = box.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => (k.current = Math.min(1, e.contentRect.width / 560)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return (
    <div
      ref={box}
      className="hairline-grid relative h-[440px] overflow-hidden  border border-line bg-stone/50 sm:h-[480px]"
    >
      <motion.p
        style={{ opacity: headerOpacity }}
        className="absolute top-6 left-1/2 -translate-x-1/2 text-[0.68rem] font-semibold whitespace-nowrap text-bronze-deep "
      >
        {challenge.flowLabel}
      </motion.p>
      <motion.span
        aria-hidden="true"
        style={{ scaleY: lineScale, height: (n - 1) * ROW + 34, top: `calc(50% + ${1 - ((n - 1) / 2) * ROW}px)` }}
        className="absolute left-1/2 -ml-[124px] w-px origin-top bg-bronze"
      />
      <ul aria-label="Fontes regulatórias típicas">
        {challenge.sources.map((s, i) => (
          <Chip key={s} label={s} i={i} n={n} p={p} k={k} />
        ))}
      </ul>
    </div>
  )
}

export function Challenge() {
  return (
    <section id="desafio" className="relative pt-24 pb-10 sm:pt-32 sm:pb-12">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="grid items-center gap-14 lg:grid-cols-[1fr_1fr] lg:gap-20">
          <div>
            <Eyebrow>{challenge.eyebrow}</Eyebrow>
            <MaskedTitle
              text={challenge.title}
              className="font-display mt-5 text-[2.1rem] leading-[1.08] text-obsidian sm:text-[2.9rem]"
            />
            <Reveal delay={0.1}>
              <p className="mt-6 max-w-xl text-[1.05rem] leading-relaxed text-ink-soft">{challenge.body}</p>
            </Reveal>
            <Reveal delay={0.2}>
              <div className="mt-10 max-w-xl border-l-2 border-bronze pl-5">
                <p className="text-[0.72rem] font-semibold text-bronze-deep ">
                  {challenge.need.label}
                </p>
                <p className="font-display mt-2 text-[1.3rem] leading-snug text-obsidian">{challenge.need.text}</p>
              </div>
            </Reveal>
          </div>
          <SourceField />
        </div>

        <ol className="mt-20 grid gap-10 border-t border-line pt-10 sm:grid-cols-3 sm:gap-8">
          {challenge.points.map((pt, i) => (
            <motion.li
              key={pt.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '0px 0px -10% 0px' }}
              transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: i * 0.1 }}
            >
                <span className="font-display text-sm text-bronze-deep tabular-nums">0{i + 1}</span>
                <h3 className="font-display mt-2 text-[1.35rem] text-obsidian">{pt.title}</h3>
                <p className="mt-2 text-[0.95rem] leading-relaxed text-ink-soft">{pt.text}</p>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  )
}
