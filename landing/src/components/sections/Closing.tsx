import { useRef } from 'react'
import { motion, useMotionTemplate, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { closing, contact, nav } from '../../content/site'
import { ButtonLink } from '../ui/Button'
import { Logo } from '../ui/Logo'
import { Eyebrow, MaskedTitle, Reveal } from '../ui/Reveal'

export function Closing() {
  const reduce = useReducedMotion()
  const ref = useRef<HTMLElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'start 0.15'] })
  // O painel nasce como cartão recuado e se expande até ocupar toda a largura.
  const inset = useTransform(scrollYProgress, [0, 1], [reduce ? 0 : 28, 0])
  const radius = useTransform(scrollYProgress, [0, 1], [reduce ? 0 : 36, 0])
  const clipPath = useMotionTemplate`inset(0px ${inset}px 0px ${inset}px round ${radius}px ${radius}px 0px 0px)`
  const mailto = `mailto:${contact.email}?subject=${encodeURIComponent(contact.subject)}`

  return (
    <motion.footer id="contato" data-dark ref={ref} style={{ clipPath }} className="on-dark relative overflow-hidden bg-obsidian text-ivory">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-1/3 right-[-15%] h-[160%] w-[50%] rotate-[24deg] bg-[linear-gradient(90deg,transparent,rgb(182_163_139/0.13),transparent)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-1/2 -left-1/4 h-full w-2/3 rounded-full bg-[radial-gradient(circle,rgb(40_75_99/0.5),transparent_65%)]"
      />

      <div className="relative mx-auto max-w-7xl px-5 pt-28 pb-12 sm:px-8 sm:pt-36">
        <div className="max-w-3xl">
          <Eyebrow tone="light">{closing.eyebrow}</Eyebrow>
          <MaskedTitle
            text={closing.title}
            className="font-display mt-6 text-[2.5rem] leading-[1.04] sm:text-[3.8rem]"
          />
          <Reveal delay={0.15}>
            <p className="mt-6 max-w-xl text-[1.06rem] leading-relaxed text-ivory/70">{closing.text}</p>
          </Reveal>
          <Reveal delay={0.25}>
            <div className="mt-10 flex flex-wrap items-center gap-3">
              <ButtonLink href={mailto} variant="bronze">
                {closing.primary}
              </ButtonLink>
              <ButtonLink href={closing.secondary.href} variant="ghost-dark" arrow={false}>
                {closing.secondary.label}
              </ButtonLink>
            </div>
            <p className="mt-4 text-[0.82rem] text-ivory/50">
              ou escreva para{' '}
              <a href={mailto} className="text-ivory/80 underline decoration-bronze/60 underline-offset-4 hover:text-ivory">
                {contact.email}
              </a>
            </p>
          </Reveal>
        </div>

        <div className="mt-28 grid gap-8 border-t border-ivory/10 pt-10 md:grid-cols-[auto_1fr_auto] md:items-start md:gap-14">
          <Logo tone="light" />
          <div className="space-y-2 text-[0.8rem] leading-relaxed text-ivory/50">
            <p className="text-ivory/70">
              © {new Date().getFullYear()} {closing.footer.rights}
            </p>
            <p className="max-w-xl">{closing.footer.disclaimer}</p>
          </div>
          <nav aria-label="Rodapé">
            <ul className="grid grid-cols-2 gap-x-8 gap-y-2 text-[0.82rem] text-ivory/60 md:grid-cols-1">
              {nav.links.map((l) => (
                <li key={l.href}>
                  <a href={l.href} className="transition-colors hover:text-ivory">
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>
    </motion.footer>
  )
}
