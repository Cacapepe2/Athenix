import { motion, useTransform, type MotionValue } from 'motion/react'
import { Bell, CalendarClock, ChevronRight, FileText, Gauge, Layers, ListChecks, UsersRound } from 'lucide-react'
import { LogoMark } from '../ui/Logo'
import { Tag } from './Tag'
import { articleById, demoNorm, obligations } from '../../content/demo'
import { splitAnchor } from '../../lib/text'

const ease = [0.16, 1, 0.3, 1] as const

const rows = [
  { Icon: CalendarClock, title: 'Prazos', detail: '48 h por evento · contínuo · anual (1 pendente)' },
  { Icon: UsersRound, title: 'Responsáveis sugeridos', detail: 'Operação · Regulatório · TI' },
  { Icon: Gauge, title: 'Impactos preliminares', detail: 'Regulatório · Operacional · Reputacional' },
]

/** Painel ilustrativo do produto (dados fictícios). Decorativo para leitores de tela; o conteúdo está no texto da página. */
export function HeroMockup({ px, py }: { px: MotionValue<number>; py: MotionValue<number> }) {
  const nearX = useTransform(px, [-0.5, 0.5], [-16, 16])
  const nearY = useTransform(py, [-0.5, 0.5], [-12, 12])
  const farX = useTransform(px, [-0.5, 0.5], [10, -10])
  const farY = useTransform(py, [-0.5, 0.5], [8, -8])
  const first = obligations[0]
  const excerpt = splitAnchor(articleById(first.articleId).text, first.anchor)!

  return (
    <div className="relative" aria-hidden="true">
      <div className="rounded-[22px] border border-white/70 bg-white/55 p-1.5 shadow-float backdrop-blur-sm">
        <div className="grid grid-cols-[52px_1fr] overflow-hidden rounded-[17px] border border-line/70 bg-ivory">
          <div className="flex flex-col items-center gap-4 bg-obsidian py-4 text-ivory/45">
            <LogoMark className="mb-2 h-6 w-6 text-ivory" />
            {[Layers, Bell, ListChecks, Gauge, UsersRound].map((Icon, i) => (
              <span
                key={i}
                className={`grid h-8 w-8 place-items-center rounded-lg ${i === 0 ? 'bg-ivory/10 text-ivory' : ''}`}
              >
                <Icon className="h-4 w-4" />
              </span>
            ))}
          </div>

          <div className="min-w-0 p-4 sm:p-5">
            <p className="text-[0.66rem] text-ink-soft">Monitoramento › Publicações</p>
            <div className="mt-1.5 flex items-start justify-between gap-3">
              <p className="font-display text-[1.15rem] leading-tight text-obsidian sm:text-[1.3rem]">
                {demoNorm.kind} {demoNorm.number}
              </p>
              <Tag kind="fictional" label="Ilustrativo" />
            </div>
            <p className="mt-1 line-clamp-1 text-[0.7rem] text-ink-soft">{demoNorm.subject}</p>

            <div className="mt-3 flex gap-4 border-b border-line text-[0.7rem] text-ink-soft">
              {['Visão geral', 'Obrigações (3)', 'Prazos', 'Impactos'].map((t, i) => (
                <span
                  key={t}
                  className={`-mb-px pb-2 whitespace-nowrap ${
                    i === 0 ? 'border-b-2 border-slate-blue font-semibold text-obsidian' : i > 2 ? 'hidden sm:inline' : ''
                  }`}
                >
                  {t}
                </span>
              ))}
            </div>

            <div className="mt-3 grid gap-2.5 sm:grid-cols-[0.85fr_1.15fr]">
              <div className="flex flex-col justify-between rounded-xl bg-stone/80 p-3.5">
                <FileText className="h-5 w-5 text-bronze-deep" strokeWidth={1.6} />
                <div className="mt-3">
                  <p className="font-display text-[1.05rem] leading-tight text-obsidian">3 obrigações candidatas</p>
                  <p className="mt-1 text-[0.66rem] leading-snug text-ink-soft">
                    Cada uma ligada ao trecho que a fundamenta.
                  </p>
                  <Tag kind="review" className="mt-2" />
                </div>
              </div>
              <div className="space-y-2">
                {rows.map(({ Icon, title, detail }, i) => (
                  <motion.div
                    key={title}
                    initial={{ opacity: 0, x: 16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.7, ease, delay: 1.1 + i * 0.12 }}
                    className="flex items-center gap-2.5 rounded-lg border border-line/80 bg-white px-3 py-2"
                  >
                    <Icon className="h-4 w-4 shrink-0 text-slate-blue" strokeWidth={1.8} />
                    <span className="min-w-0 flex-1">
                      <span className="block text-[0.7rem] font-semibold text-obsidian">{title}</span>
                      <span className="block truncate text-[0.62rem] text-ink-soft">{detail}</span>
                    </span>
                    <ChevronRight className="h-3.5 w-3.5 text-ink-soft/60" />
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="mt-2.5 rounded-lg border border-line/80 bg-white p-3">
              <div className="flex items-center justify-between gap-2">
                <Tag kind="source" />
                <span className="text-[0.62rem] text-ink-soft">{articleById(first.articleId).label}</span>
              </div>
              <p className="mt-1.5 line-clamp-2 text-[0.68rem] leading-relaxed text-ink-soft">
                {excerpt[0]}
                <mark className="rounded-[2px] bg-bronze/35 text-obsidian">{excerpt[1]}</mark>
                {excerpt[2]}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Camadas flutuantes: profundidade e parallax opostos ao ponteiro */}
      <motion.div style={{ x: farX, y: farY }} className="absolute -top-12 left-4 hidden sm:-left-8 sm:block">
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.94 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8, ease, delay: 1.5 }}
        className="flex items-center gap-2.5 rounded-xl border border-line/70 bg-white/95 px-3.5 py-2.5 shadow-soft"
      >
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-slate-blue/50" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-slate-blue" />
        </span>
        <span>
          <span className="block text-[0.68rem] font-semibold text-obsidian">Nova publicação detectada</span>
          <span className="block text-[0.6rem] text-ink-soft">Documento original preservado · {demoNorm.fingerprint}</span>
        </span>
      </motion.div>
      </motion.div>

      <motion.div style={{ x: nearX, y: nearY }} className="absolute -right-3 -bottom-8 hidden w-60 sm:block lg:-right-8">
      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.94 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8, ease, delay: 1.8 }}
        className="rounded-xl border border-line/70 bg-white p-3.5 shadow-float"
      >
        <div className="flex items-center justify-between">
          <span className="text-[0.6rem] font-semibold tracking-[0.14em] text-bronze-deep uppercase">Obrigação 1</span>
          <Tag kind="ai" label="IA" />
        </div>
        <p className="mt-1.5 text-[0.76rem] leading-snug font-semibold text-obsidian">{first.title}</p>
        <p className="mt-2 flex items-center gap-1.5 text-[0.62rem] text-ink-soft">
          <span className="h-px w-3 bg-bronze" />
          Fundamento: {articleById(first.articleId).label} · trecho literal
        </p>
      </motion.div>
      </motion.div>
    </div>
  )
}
