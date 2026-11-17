import { motion } from 'motion/react'
import { ArrowRight, Building, Compass, ShieldCheck, Target, TrendingUp, UsersRound } from 'lucide-react'
import { business } from '../../content/site'
import { Eyebrow, MaskedTitle, Reveal } from '../ui/Reveal'

const icons = [Target, Compass, UsersRound, Building, ShieldCheck, TrendingUp]
const ease = [0.16, 1, 0.3, 1] as const

/** As seis perguntas do negócio num painel único; cada célula leva à seção que aprofunda a resposta. */
export function BusinessSummary() {
  return (
    <section id="negocio" className="relative pt-6 pb-10 sm:pb-14">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_1fr] lg:items-end">
          <div>
            <Eyebrow>{business.eyebrow}</Eyebrow>
            <MaskedTitle
              text={business.title}
              className="font-display mt-5 text-[2.1rem] leading-[1.08] text-obsidian sm:text-[2.6rem]"
            />
          </div>
          <Reveal delay={0.1}>
            <p className="max-w-xl text-[1rem] leading-relaxed text-ink-soft lg:justify-self-end">{business.intro}</p>
          </Reveal>
        </div>

        {/* Grade com filetes de 1px: um painel único em vez de seis cartões soltos */}
        <ol className="mt-10 grid gap-px overflow-hidden rounded-[26px] border border-line bg-line shadow-soft sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {business.items.map((item, i) => {
            const Icon = icons[i]
            return (
              <motion.li
                key={item.question}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '0px 0px -8% 0px' }}
                transition={{ duration: 0.8, ease, delay: i * 0.08 }}
                className="group relative flex flex-col bg-ivory p-6 transition-colors duration-500 hover:bg-white"
              >
                <div className="flex items-center justify-between">
                  <Icon
                    aria-hidden="true"
                    strokeWidth={1.5}
                    className="h-6 w-6 text-bronze-deep transition-transform duration-500 ease-out-expo group-hover:-translate-y-0.5"
                  />
                  <span className="font-display text-sm text-ink-soft/60 tabular-nums">0{i + 1}</span>
                </div>
                <h3 className="font-display mt-6 text-[1.22rem] leading-[1.15] text-obsidian">{item.question}</h3>
                <span
                  aria-hidden="true"
                  className="mt-3 block h-px w-8 origin-left bg-bronze transition-transform duration-500 ease-out-expo group-hover:scale-x-[2.5]"
                />
                <p className="mt-3 flex-1 text-[0.88rem] leading-relaxed text-ink-soft">{item.answer}</p>
                <a
                  href={item.href}
                  className="mt-5 inline-flex items-center gap-1.5 self-start text-[0.8rem] font-medium text-slate-blue hover:text-obsidian"
                >
                  {business.more}
                  <span className="sr-only">: {item.question}</span>
                  <ArrowRight aria-hidden="true" className="h-3.5 w-3.5 transition-transform duration-300 group-hover:translate-x-0.5" />
                </a>
              </motion.li>
            )
          })}
        </ol>

        <Reveal delay={0.2}>
          <p className="mt-5 inline-flex items-center gap-2 text-[0.78rem] text-bronze-deep">
            <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-bronze-deep" />
            {business.note}
          </p>
        </Reveal>
      </div>
    </section>
  )
}
