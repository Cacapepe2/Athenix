import { motion } from 'motion/react'
import { demoNorm, type Article } from '../../content/demo'
import { splitAnchor } from '../../lib/text'

interface Props {
  /** articleId -> trecho literal a realçar */
  marks?: Record<string, string>
  /** número exibido ao lado de cada realce (articleId -> nº) */
  markLabels?: Record<string, string>
  focusId?: string
  animateMarks?: boolean
  articles?: Article[]
  className?: string
}

/** Página do documento original; realça somente trechos literais (rastreabilidade). */
export function DocumentView({ marks = {}, markLabels = {}, focusId, animateMarks, articles, className = '' }: Props) {
  const list = articles ?? demoNorm.articles
  return (
    <div className={`paper rounded-xl border border-line p-5 text-[0.8rem] leading-relaxed text-ink-soft ${className}`}>
      <div className="mb-3 border-b border-line pb-3">
        <p className="text-[0.62rem] font-semibold tracking-[0.18em] text-bronze-deep uppercase">
          {demoNorm.issuer}
        </p>
        <p className="font-display mt-1 text-[1.05rem] leading-tight text-obsidian">
          {demoNorm.kind} {demoNorm.number}
        </p>
      </div>
      <div className="space-y-2.5">
        {list.map((a) => {
          const parts = marks[a.id] ? splitAnchor(a.text, marks[a.id]) : null
          const dim = focusId && focusId !== a.id
          return (
            <p key={a.id} className={`transition-opacity duration-500 ${dim ? 'opacity-40' : ''}`}>
              {/* Texto real já traz o próprio rótulo ("Art. 9º ..."): não repete. */}
              {!a.text.startsWith(a.label) && !(a.label.startsWith('item ') && a.text.startsWith(a.label.slice(5) + '.')) && <span className="mr-1 font-semibold text-obsidian">{a.label}</span>}
              {parts ? (
                <>
                  {parts[0]}
                  <span>
                    {/* background-size atravessa quebras de linha, ao contrário de um overlay absoluto */}
                    <motion.mark
                      className="rounded-[2px] bg-transparent bg-[linear-gradient(rgb(182_163_139/0.4),rgb(182_163_139/0.4))] bg-no-repeat text-obsidian"
                      initial={animateMarks ? { backgroundSize: '0% 100%' } : false}
                      animate={{ backgroundSize: '100% 100%' }}
                      transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
                    >
                      {parts[1]}
                    </motion.mark>
                    {markLabels[a.id] && (
                      <motion.span
                        layoutId={`mark-${a.id}`}
                        aria-hidden="true"
                        className="relative -top-2 ml-1 inline-grid h-4 w-4 place-items-center rounded-full bg-slate-blue text-[0.58rem] font-semibold text-ivory"
                      >
                        {markLabels[a.id]}
                      </motion.span>
                    )}
                  </span>
                  {parts[2]}
                </>
              ) : (
                a.text
              )}
            </p>
          )
        })}
      </div>
    </div>
  )
}
