import { motion } from 'motion/react'
import { opportunity } from '../../content/site'
import { Eyebrow, MaskedTitle, Reveal } from '../ui/Reveal'

const ease = [0.16, 1, 0.3, 1] as const

// Anéis concêntricos: núcleo = ponto de partida; anéis externos = expansão condicionada à validação.
const rings = [
  { inset: '0%', labelTop: '7%', cls: 'border border-dashed border-obsidian/25 animate-[spin_80s_linear_infinite]' },
  { inset: '17%', labelTop: '24%', cls: 'border border-obsidian/20 bg-white/50' },
  { inset: '34%', labelTop: '50%', cls: 'bg-slate-blue shadow-float' },
]

function Rings() {
  const [core, mid, outer] = opportunity.rings
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[480px]">
      {rings.map((r, i) => (
        <motion.div
          key={i}
          aria-hidden="true"
          initial={{ opacity: 0, scale: 0.7 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: '0px 0px -10% 0px' }}
          transition={{ duration: 1.2, ease, delay: 0.5 - i * 0.2 }}
          style={{ inset: r.inset }}
          className={`absolute rounded-full ${r.cls}`}
        />
      ))}
      <ol className="contents">
        {[core, mid, outer].map((l, i) => {
          const pos = rings[2 - i]
          const isCore = i === 0
          return (
            <motion.li
              key={l.label}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease, delay: 0.7 + i * 0.25 }}
              style={{ top: pos.labelTop }}
              className={`absolute left-1/2 -translate-x-1/2 -translate-y-1/2 text-center ${isCore ? 'w-[27%]' : 'w-[42%]'}`}
            >
              <span
                className={`block text-[0.62rem] font-semibold tracking-[0.14em] ${isCore ? 'text-bronze' : 'text-bronze-deep'}`}
              >
                {l.tag}
              </span>
              <span
                className={`font-display mt-0.5 block leading-tight ${isCore ? 'text-[0.95rem] text-ivory sm:text-[1.1rem]' : 'text-[0.9rem] text-obsidian sm:text-[1.05rem]'}`}
              >
                {l.label}
              </span>
            </motion.li>
          )
        })}
      </ol>
    </div>
  )
}

export function Opportunity() {
  return (
    <section id="oportunidade" className="overflow-hidden py-24 sm:py-32">
      <div className="mx-auto grid max-w-7xl items-center gap-16 px-5 sm:px-8 lg:grid-cols-[1fr_1fr]">
        <div>
          <Eyebrow>{opportunity.eyebrow}</Eyebrow>
          <MaskedTitle
            text={opportunity.title}
            className="font-display mt-5 text-[2.1rem] leading-[1.08] text-obsidian sm:text-[2.9rem]"
          />
          <div className="mt-6 space-y-4">
            {opportunity.paragraphs.map((p, i) => (
              <Reveal key={i} delay={0.08 * i}>
                <p className="max-w-xl text-[1.02rem] leading-relaxed text-ink-soft">{p}</p>
              </Reveal>
            ))}
          </div>
          <Reveal delay={0.3}>
            <p className="mt-8 inline-flex items-center gap-2 rounded-full border border-dashed border-bronze-deep/45 px-3.5 py-1.5 text-[0.78rem] font-medium text-bronze-deep">
              <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-bronze-deep" />
              {opportunity.hypothesis}
            </p>
          </Reveal>
        </div>
        <Rings />
      </div>
    </section>
  )
}
