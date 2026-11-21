import { useRef } from 'react'
import { motion, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { Check } from 'lucide-react'
import { hero } from '../../content/site'
import { ButtonLink } from '../ui/Button'
import { Eyebrow } from '../ui/Reveal'
import { HeroMockup } from '../product/HeroMockup'
import { usePointerTilt } from '../../hooks/usePointerTilt'

const ease = [0.16, 1, 0.3, 1] as const

export function Hero() {
  const reduce = useReducedMotion()
  const section = useRef<HTMLElement>(null)
  const { scrollYProgress } = useScroll({ target: section, offset: ['start start', 'end start'] })
  const mockY = useTransform(scrollYProgress, [0, 1], [0, reduce ? 0 : 90])
  const textY = useTransform(scrollYProgress, [0, 1], [0, reduce ? 0 : 40])
  const tilt = usePointerTilt(5)
  const fim = hero.titleLines.length - 1
  const palavras = hero.titleLines[fim].split(' ')
  const [lead, last] = [palavras.slice(0, -1).join(' '), palavras.at(-1)]

  return (
    <section
      id="topo"
      ref={section}
      className="relative overflow-hidden bg-ivory pt-28 pb-24 sm:pt-36 lg:pb-32"
      {...tilt.handlers}
    >
      {/* Fundo: grade fina e faixa de luz diagonal, como no material de referência */}

      <div className="relative mx-auto grid max-w-7xl items-center gap-16 px-5 sm:px-8 lg:grid-cols-[1.12fr_1fr] lg:gap-10">
        <motion.div style={{ y: textY }}>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1, delay: 0.1 }}>
            <Eyebrow>{hero.eyebrow}</Eyebrow>
          </motion.div>

          <h1 className="font-display mt-6 text-[2.3rem] leading-[1.06] font-normal text-obsidian sm:text-[3rem] lg:text-[2.35rem] xl:text-[2.65rem]">
            {hero.titleLines.map((line, i) => (
              <span key={line} className="block overflow-hidden pb-[0.08em]">
                <motion.span
                  className="block"
                  initial={{ y: '110%' }}
                  animate={{ y: '0%' }}
                  transition={{ duration: 1.1, ease, delay: 0.2 + i * 0.12 }}
                >
                  {i === fim ? (
                    <>
                      {lead} <em className="text-slate-blue">{last}</em>
                    </>
                  ) : (
                    line
                  )}
                </motion.span>
              </span>
            ))}
          </h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease, delay: 0.55 }}
            className="mt-6 max-w-xl text-[1.06rem] leading-relaxed text-ink-soft sm:text-[1.12rem]"
          >
            {hero.subtitle}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease, delay: 0.7 }}
            className="mt-9 flex flex-wrap items-center gap-3"
          >
            <ButtonLink href={hero.primary.href}>{hero.primary.label}</ButtonLink>
            <ButtonLink href={hero.secondary.href} variant="secondary" arrow={false}>
              {hero.secondary.label}
            </ButtonLink>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 0.95 }}
            className="mt-10 border-t border-obsidian/10 pt-6"
          >
            <p className="inline-flex items-center gap-2 border border-dashed border-bronze-deep/40 px-3 py-1 text-[0.75rem] font-medium text-bronze-deep">
              <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-bronze-deep" />
              {hero.status}
            </p>
            <ul className="mt-4 grid gap-2 text-[0.85rem] text-ink-soft sm:grid-cols-3 sm:gap-4">
              {hero.principles.map((p) => (
                <li key={p} className="flex items-start gap-2">
                  <Check aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-blue" strokeWidth={2.4} />
                  {p}
                </li>
              ))}
            </ul>
          </motion.div>
        </motion.div>

        <motion.div style={{ y: mockY }} className="[perspective:1600px]">
          <motion.div
            ref={tilt.ref}
            initial={{ opacity: 0, y: 70, rotateX: 16, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, rotateX: 0, scale: 1 }}
            transition={{ duration: 1.5, ease, delay: 0.35 }}
          >
            <motion.div style={{ rotateX: tilt.rotateX, rotateY: tilt.rotateY, transformStyle: 'preserve-3d' }}>
              <HeroMockup px={tilt.px} py={tilt.py} />
            </motion.div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
