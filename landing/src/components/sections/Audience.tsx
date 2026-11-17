import { motion } from 'motion/react'
import { Building, Fuel, RadioTower, Zap } from 'lucide-react'
import { audience } from '../../content/site'
import { Eyebrow, MaskedTitle, Reveal } from '../ui/Reveal'

const sectorIcons = [Zap, RadioTower, Fuel, Building]
const ease = [0.16, 1, 0.3, 1] as const

export function Audience() {
  return (
    <section id="para-quem" className="overflow-x-clip py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="grid gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20">
          <div className="lg:sticky lg:top-28 lg:self-start">
            <Eyebrow>{audience.eyebrow}</Eyebrow>
            <MaskedTitle
              text={audience.title}
              className="font-display mt-5 text-[2.1rem] leading-[1.08] text-obsidian sm:text-[2.9rem]"
            />
            <Reveal delay={0.1}>
              <p className="mt-6 max-w-md text-[1.02rem] leading-relaxed text-ink-soft">{audience.description}</p>
            </Reveal>
          </div>

          <ul aria-label="Público-alvo">
            {audience.roles.map((r, i) => (
              <motion.li
                key={r.title}
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '0px 0px -10% 0px' }}
                transition={{ duration: 0.8, ease, delay: i * 0.07 }}
                className="group relative grid gap-1 border-t border-line py-6 last:border-b sm:grid-cols-[0.85fr_1.15fr] sm:gap-8"
              >
                <span
                  aria-hidden="true"
                  className="absolute top-[-1px] left-0 h-px w-full origin-left scale-x-0 bg-bronze-deep transition-transform duration-700 ease-out-expo group-hover:scale-x-100"
                />
                <h3 className="font-display text-[1.45rem] leading-tight text-obsidian transition-transform duration-500 ease-out-expo group-hover:translate-x-1.5">
                  {r.title}
                </h3>
                <p className="text-[0.95rem] leading-relaxed text-ink-soft sm:pt-1">{r.text}</p>
              </motion.li>
            ))}
          </ul>
        </div>

        <div id="potenciais-clientes" className="mt-24">
          <p className="text-[0.72rem] font-semibold tracking-[0.2em] text-bronze-deep uppercase">{audience.sectorsTitle}</p>
          {/* As frentes futuras "desdobram" a partir do foco inicial */}
          <ul className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-[1.25fr_1fr_1fr_1fr]">
            {audience.sectors.map((s, i) => {
              const Icon = sectorIcons[i]
              return (
                <motion.li
                  key={s.title}
                  initial={{ opacity: 0, x: i === 0 ? 0 : -60 * i, scale: i === 0 ? 0.96 : 1 }}
                  whileInView={{ opacity: 1, x: 0, scale: 1 }}
                  viewport={{ once: true, margin: '0px 0px -10% 0px' }}
                  transition={{ duration: 1, ease, delay: i === 0 ? 0 : 0.3 + i * 0.12 }}
                  className={`relative flex flex-col rounded-2xl p-6 ${
                    s.now
                      ? 'bg-slate-blue text-ivory shadow-float'
                      : 'border border-dashed border-obsidian/20 bg-white/40 text-obsidian'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <Icon
                      aria-hidden="true"
                      className={`h-6 w-6 ${s.now ? 'text-bronze' : 'text-bronze-deep'}`}
                      strokeWidth={1.5}
                    />
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[0.68rem] font-medium ${
                        s.now ? 'bg-ivory/15 text-ivory' : 'bg-stone text-ink-soft'
                      }`}
                    >
                      {s.tag}
                    </span>
                  </div>
                  <h3 className="font-display mt-8 text-[1.3rem] leading-tight">{s.title}</h3>
                  <p className={`mt-1.5 text-[0.88rem] leading-snug ${s.now ? 'text-ivory/75' : 'text-ink-soft'}`}>{s.text}</p>
                </motion.li>
              )
            })}
          </ul>
        </div>
      </div>
    </section>
  )
}
